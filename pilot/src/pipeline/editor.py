"""Editor scaffold: the turn loop that lets the fixed editor model carry out
one change request on a program. Provisional, pending team sign-off; it is
isolated here and selected by editor.scaffold in the config.

Each turn builds a fresh, self-contained prompt from the editor template:
the current change request only, the current files, the allowed file names,
the turns left, and the result of the previous turn (check output or an
error). Nothing else accumulates, so the prompt stays bounded no matter how
many turns run; the check output is cut to editor.max_check_output_chars.

The editor replies with full-file replacements in the parser's fence format
and/or one command on its own line:
- RUN_CHECKS: apply the files and run the public checks (initial plus
  changes 1..k) in the sandbox; the output comes back next turn.
- DONE: apply the files and finish.
A reply that is cut off (finish_reason "length"), that breaks the format,
that writes a file outside the original program's allowlist, or that has
neither files nor a command is a wasted turn: nothing from it is applied,
and the next prompt says what was wrong. Never a crash.

The step ends with status "done", "budget_exhausted" (turns, total tokens,
wall time, or a program too large for the prompt) or "infra_error" (the
model call or the sandbox failed; never scored). The editor never sees
private tests or later changes: they are not inputs to this module.

Usage:
    editor = Editor(cfg.editor, evaluator)
    backend = CachedBackend(make_backend(cfg.editor.backend, rep_seed), store)  # one per trial
    outcome = editor.edit(backend, program, task.sequence("s1").steps[0])
    outcome.status, outcome.program, outcome.tokens_in, outcome.diff_lines
"""

from __future__ import annotations

import difflib
import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from .backends import Backend, BackendError
from .config import EditorConfig
from .evaluator import CategoryResult, Evaluator
from .parser import parse_program, prose_lines, render_program
from .registry import Program, Step, load_template

EditStatus = Literal["done", "budget_exhausted", "infra_error"]
TEMPLATE_FIELDS = frozenset({"request", "files", "feedback", "allowed_files", "turns_left"})
RUN_CHECKS, DONE = "RUN_CHECKS", "DONE"

FIRST_FEEDBACK = "Nothing yet: this is your first turn."
APPLIED = "Your files were applied. Send RUN_CHECKS to test them, or DONE to finish."
REMINDER = (
    "Reply with complete files as ```python file=<path> blocks and/or RUN_CHECKS or "
    "DONE on a line by itself, outside any code block."
)
CUT_OFF = (
    "Your last reply was cut off at the length limit, so nothing from it was applied. "
    "Send shorter replies: only the files you change. " + REMINDER
)


@dataclass(frozen=True)
class EditOutcome:
    status: EditStatus
    program: Program  # the files after the step (everything applied so far)
    reason: str  # done, max_turns, max_total_tokens, wall_time, prompt_too_large, or an error
    turns: int  # replies received
    wasted_turns: int  # replies that applied nothing and ran nothing
    model_calls: int  # generate() calls (cached replays included)
    tokens_in: int
    tokens_out: int
    wall_s: float
    diff_lines: int  # lines added plus lines removed, over all files
    infra_cause: str = ""  # backend_error, or the sandbox's cause code


class Editor:
    def __init__(
        self,
        cfg: EditorConfig,
        evaluator: Evaluator,
        *,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if cfg.view_transform != "none":
            raise NotImplementedError(f"view_transform {cfg.view_transform!r}")
        self.cfg = cfg
        self.evaluator = evaluator
        self.template = load_template(cfg.prompt_template, TEMPLATE_FIELDS)
        self._clock = clock  # injectable so wall-time tests don't sleep

    def edit(self, backend: Backend, program: Program, step: Step) -> EditOutcome:
        """Run the turn loop for one change; never raises for anything the
        model does."""
        budget = self.cfg.budget
        start = self._clock()
        allowed = sorted(program)  # the editor may only rewrite these files
        files = dict(program)
        feedback = FIRST_FEEDBACK
        turns = wasted = calls = tokens_in = tokens_out = 0

        def finish(status: EditStatus, reason: str, cause: str = "") -> EditOutcome:
            return EditOutcome(
                status=status,
                program=dict(files),
                reason=reason,
                turns=turns,
                wasted_turns=wasted,
                model_calls=calls,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                wall_s=self._clock() - start,
                diff_lines=diff_lines(program, files),
                infra_cause=cause,
            )

        while True:
            # Budgets are checked before each call; a reply already received
            # is always processed.
            if turns >= budget.max_turns:
                return finish("budget_exhausted", "max_turns")
            if tokens_in + tokens_out >= budget.max_total_tokens:
                return finish("budget_exhausted", "max_total_tokens")
            if self._clock() - start >= budget.wall_time_s:
                return finish("budget_exhausted", "wall_time")

            prompt = self.build_prompt(step, files, feedback, allowed, budget.max_turns - turns)
            if len(prompt) > self.cfg.max_prompt_chars:
                return finish("budget_exhausted", "prompt_too_large")
            try:
                reply = backend.generate(prompt)
            except BackendError as exc:
                return finish("infra_error", str(exc), cause="backend_error")
            turns += 1
            calls += 1
            usage = backend.last_usage
            finish_reason = usage.finish_reason if usage else None
            tokens_in += _tokens(usage.prompt_tokens if usage else None, prompt)
            tokens_out += _tokens(usage.completion_tokens if usage else None, reply)

            if finish_reason == "length":
                wasted += 1
                feedback = CUT_OFF  # never apply a half-written file
                continue
            parsed = parse_program(reply, allowed, finish_reason, require_all=False)
            if not parsed.ok:
                wasted += 1
                feedback = f"Nothing was applied: {parsed.failure.detail}. {REMINDER}"
                continue
            commands = {line for line in prose_lines(reply) if line in (RUN_CHECKS, DONE)}
            if not parsed.files and not commands:
                wasted += 1
                feedback = f"Your reply had no files and no command. {REMINDER}"
                continue

            files.update(parsed.files)
            if DONE in commands:
                return finish("done", "done")
            if RUN_CHECKS in commands:
                result = self.evaluator.run_category(files, step.tests.public, "public")
                if result.status == "infra_error":
                    return finish("infra_error", result.detail, cause=result.infra_cause)
                feedback = self.check_feedback(result)
            else:
                feedback = APPLIED

    def build_prompt(
        self, step: Step, files: Program, feedback: str, allowed: list[str], turns_left: int
    ) -> str:
        """The whole prompt for one turn. Its inputs are the current change's
        request, the current files and the last feedback; nothing about
        private tests or later changes is passed in."""
        return self.template.substitute(
            request=step.change.request.strip(),
            files=render_program(dict(files)).strip(),
            feedback=feedback,
            allowed_files=", ".join(allowed),
            turns_left=turns_left,
        )

    def check_feedback(self, result: CategoryResult) -> str:
        """Public check results for the next prompt, cut to the configured
        size (the middle goes first; the start and the summary at the end of
        pytest's output are the most useful parts)."""
        if result.total:
            head = f"Public checks: {result.passed} of {result.total} passed."
        else:
            head = "Public checks: no test ran (the program may fail to import)."
        if result.run_status in ("timeout", "oom"):
            head += f" The run was stopped by {result.run_status}."
        failing = [f"- {c.node_id}: {c.outcome}" for c in result.cases if c.outcome != "passed"]
        output = normalize_output(result.output.strip())
        text = "\n".join([head, *failing, "", "pytest output:", output])
        return _truncate_middle(text, self.cfg.max_check_output_chars)


_DURATION = re.compile(r"\bin \d+(?:\.\d+)?s(?: \(\d+:\d\d:\d\d\))?")
_ADDRESS = re.compile(r"\b0x[0-9a-fA-F]{4,}\b")


def normalize_output(text: str) -> str:
    """Remove what varies between identical runs: pytest's durations ("in
    0.31s") and memory addresses ("at 0x7f3a..."). The next prompt includes
    this text, and a replayed trial only hits the call cache if its prompts
    are byte-identical to the recorded ones."""
    return _ADDRESS.sub("0x...", _DURATION.sub("in <time>", text))


def diff_lines(before: Program, after: Program) -> int:
    """Lines added plus lines removed across all files."""
    count = 0
    for path in sorted(set(before) | set(after)):
        old = before.get(path, b"").decode("utf-8", "replace").splitlines()
        new = after.get(path, b"").decode("utf-8", "replace").splitlines()
        for line in difflib.unified_diff(old, new, lineterm="", n=0):
            if line[:1] in "+-" and not line.startswith(("+++", "---")):
                count += 1
    return count


def _tokens(reported: int | None, text: str) -> int:
    """Token count from the backend, or about 4 characters per token when the
    backend doesn't report usage."""
    return reported if reported is not None else len(text) // 4


def _truncate_middle(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    marker = "\n[... output truncated ...]\n"
    keep = max(0, limit - len(marker))
    return text[: keep // 2] + marker + text[len(text) - (keep - keep // 2) :]
