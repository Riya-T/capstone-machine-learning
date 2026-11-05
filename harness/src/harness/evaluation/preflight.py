"""Check evaluation readiness without generating code or creating a collection run.

Usage:
    check_preflight(prepared, probe=False)
    # Probing only reads Docker state and configured local servers' model lists.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import urllib.error
import urllib.request

from .plan import _local_only, preview
from .records import EvaluationError


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise EvaluationError("Model-list redirects are not followed")


def _models(url):
    # Never send a prompt, API key or POST request during a readiness check.
    request = urllib.request.Request(url.rstrip("/") + "/models", method="GET")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    with opener.open(request, timeout=3) as response:
        data = response.read(2 * 1024 * 1024 + 1)
    if len(data) > 2 * 1024 * 1024:
        raise EvaluationError("Model list exceeds the preflight response limit")
    body = json.loads(data)
    return {row["id"] for row in body["data"] if isinstance(row.get("id"), str)}


def _docker(*arguments):
    process = subprocess.run(["docker", *arguments], capture_output=True, text=True, timeout=10)
    if process.returncode:
        raise EvaluationError("Docker inspection failed; check the daemon and configured image")
    return process.stdout.strip()


def check_preflight(prepared, *, probe=False):
    checks = []

    def record(name, status, detail):
        checks.append(dict(check=name, status=status, detail=detail))

    record(
        "execution_platform",
        "pass" if os.name == "posix" else "fail",
        "Live collection requires Linux/WSL; saved-only reporting also works on Windows.",
    )
    record("docker_cli", "pass" if shutil.which("docker") else "fail", "Docker CLI availability")
    ancestor = prepared.root
    while not ancestor.exists():
        ancestor = ancestor.parent
    record(
        "output_parent",
        "pass" if os.access(ancestor, os.W_OK) else "fail",
        "Nearest existing output parent is writable; no directory was created.",
    )
    seen_servers, seen_images = {}, set()
    for method, cfg in zip(prepared.plan.methods, prepared.configs, strict=True):
        try:
            _local_only(cfg)
        except EvaluationError as error:
            record(method.id + "/backend", "fail", str(error))
            continue
        for role, backend in (("writer", cfg.writer.backend), ("editor", cfg.editor.backend)):
            name = method.id + "/" + role
            if backend.kind == "mock":
                record(name, "pass", "Mock fixture backend; no inference requested.")
                continue
            # The existing local-only guard also rejects credentials in URLs.
            endpoint = backend.base_url
            if not probe:
                record(name, "not_checked", "Use --probe to GET the local advertised model list.")
                continue
            if endpoint not in seen_servers:
                try:
                    seen_servers[endpoint] = _models(endpoint)
                except (OSError, ValueError, KeyError, TypeError, EvaluationError) as error:
                    seen_servers[endpoint] = str(type(error).__name__)
            models = seen_servers[endpoint]
            if isinstance(models, str):
                record(
                    name, "fail", f"Cannot read local model list ({models}); no generation tried."
                )
            else:
                record(
                    name,
                    "pass" if backend.model in models else "fail",
                    f"Configured model {'is' if backend.model in models else 'is not'} advertised: "
                    + backend.model,
                )
        seen_images.add(cfg.sandbox.image)
    if probe and shutil.which("docker"):
        try:
            details = json.loads(_docker("info", "--format", "{{json .}}"))
            record(
                "docker_engine",
                "pass" if details.get("OSType") == "linux" else "fail",
                "Linux engine " + str(details.get("ServerVersion")),
            )
            image_ids = set()
            for image in sorted(seen_images):
                try:
                    image_ids.add(_docker("image", "inspect", "--format", "{{.Id}}", image))
                    record(
                        "image/" + image, "pass", "Image already exists; nothing built or pulled."
                    )
                except EvaluationError:
                    record(
                        "image/" + image,
                        "fail",
                        "Image absent; explicitly build it before inference.",
                    )
            lock = prepared.root / "evaluation.lock.json"
            if lock.exists():
                from .records import read_json

                frozen = read_json(lock.read_bytes())
                record(
                    "locked_image",
                    "pass" if image_ids == {frozen.get("image_id")} else "fail",
                    "Compare existing image identity with this plan's saved lock.",
                )
        except (OSError, ValueError, subprocess.TimeoutExpired, EvaluationError) as error:
            record("docker_engine", "fail", str(error))
    else:
        record(
            "docker_engine", "not_checked", "Use --probe to inspect engine/images without building."
        )
    failures = sum(c["status"] == "fail" for c in checks)
    pending = sum(c["status"] == "not_checked" for c in checks)
    return dict(
        ready=not failures and not pending,
        failures=failures,
        unchecked=pending,
        checks=checks,
        plan=preview(prepared),
        inference_performed=False,
        note="Readiness is a snapshot. Advertised model IDs do not certify weights, quantization, "
        "context settings or future successful inference.",
    )
