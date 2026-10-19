# Sandbox image for running generated programs and their tests.
#
# Python 3.11 (pinned by digest) plus exactly the pytest and Hypothesis
# versions in uv.lock, so tests behave the same inside the sandbox as on the
# host. Dependencies are listed explicitly and installed with --no-deps, so
# nothing unpinned can slip in; `pip check` fails the build if the set is
# incomplete.
#
# Usage (from harness/):
#     docker build -t harness-sandbox:py3.11-v1 docker/sandbox
# or let the runner build it: SandboxRunner(cfg.sandbox).ensure_image()
# The tag must match `sandbox.image` in the config. Change the tag whenever
# this file changes.
FROM python:3.11-slim@sha256:e88e9763f943ec1834f992a4b51e0f24500486803e8bc534e5767af9ea65f6ce

RUN pip install --no-cache-dir --no-deps \
        pytest==9.1.1 iniconfig==2.3.1 packaging==26.3 pluggy==1.6.0 pygments==2.21.0 \
        hypothesis==6.169.1 sortedcontainers==2.4.0 \
    && pip check

# Containers run as the unprivileged `nobody` user (set by the runner).
WORKDIR /work
