"""Editor turn loop: lets the editor model make one change to a program.

Each turn the editor gets a fresh prompt with the change request, the
current files, the full result of its last turn, and a one-line summary of
each of its latest few turns (editor.history_turns). The prompt never grows
without bound, and it never contains private tests or later changes.

The editor replies with complete new files and/or one command:
- RUN_CHECKS: apply the files and run the public checks; results come next turn.
- DONE: apply the files and finish.
The step also finishes as soon as every public check passes.

A turn is wasted (nothing new applied or run, and the editor is told why)
when the reply is cut off, breaks the format, writes a file it may not
touch, has no files and no command, or changes nothing. RUN_CHECKS on code
that was already checked doesn't rerun the checks; the earlier result is
shown instead. Together with a new seed each turn, this stops the editor
from repeating the same reply until it runs out of turns, which happened
in the pilot.

A step ends as "done", "budget_exhausted" (turns, tokens, time, or a
program too big for the prompt) or "infra_error" (the model or the sandbox
failed; never scored).

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

from ..config import EditorConfig
from ..models.backends import Backend, BackendError
from ..models.parser import parse_program, prose_lines, render_program
from ..registry import Program, Step, load_template
from ..sandbox.evaluator import CategoryResult, Evaluator

EditStatus = Literal["done", "budget_exhausted", "infra_error"]
# Part of the editor result key: raise it whenever a code change alters how
# the editor behaves or what it sees, so stored trials from the old behavior
# are not reused. 1: original loop. 2: finishes when every public check
# passes; check output keeps full failure lines and short tracebacks.
# 3: per-turn seeds, turn summaries ($history), unchanged replies caught.
PROTOCOL_VERSION = 3
TEMPLATE_FIELDS = frozenset(
    {"request", "files", "feedback", "history", "allowed_files", "turns_left"}
)
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
UNCHANGED = (
    "Your files were identical to the current ones, so nothing changed. "
    "Change the code, or send DONE if the change is complete."
)
NOT_RERUN = (
    "The program has not changed since the last check, so the checks were not run "
    "again; they would fail the same way. Change the code before sending RUN_CHECKS. "
    "The last check result was:\n\n"
)
NO_HISTORY = "None yet: this is your first turn."
HISTORY_LINE_CHARS = 300  # each turn summary is cut to this length


@dataclass(frozen=True)
class EditOutcome:
    status: EditStatus
    program: Program  # the files after the step (everything applied so far)
    # done, checks_passed, max_turns, max_total_tokens, wall_time,
    # prompt_too_large, or an error message
    reason: str
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
        history: list[str] = []  # one summary line per turn
        checked: tuple[Program, str] | None = None  # files at the last check run, its feedback
        turns = wasted = calls = tokens_in = tokens_out = 0

        def note(text: str) -> None:
            history.append(_cut(f"Turn {turns}: {text}", HISTORY_LINE_CHARS))

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

            prompt = self.build_prompt(
                step, files, feedback, history, allowed, budget.max_turns - turns
            )
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
                note("reply cut off at the length limit; nothing applied")
                continue
            parsed = parse_program(reply, allowed, finish_reason, require_all=False)
            if not parsed.ok:
                wasted += 1
                feedback = f"Nothing was applied: {parsed.failure.detail}. {REMINDER}"
                note(f"reply broke the format ({parsed.failure.reason}); nothing applied")
                continue
            commands = {line for line in prose_lines(reply) if line in (RUN_CHECKS, DONE)}
            if not parsed.files and not commands:
                wasted += 1
                feedback = f"Your reply had no files and no command. {REMINDER}"
                note("reply had no files and no command; nothing applied")
                continue

            before = dict(files)
            files.update(parsed.files)
            sent = describe_files(before, files, parsed.files)
            if DONE in commands:
                return finish("done", "done")
            if RUN_CHECKS in commands:
                if checked is not None and files == checked[0]:
                    wasted += 1
                    feedback = NOT_RERUN + checked[1]
                    note(f"{sent}, then RUN_CHECKS on unchanged code; checks not run again")
                    continue
                result = self.evaluator.run_category(files, step.tests.public, "public")
                if result.status == "infra_error":
                    return finish("infra_error", result.detail, cause=result.infra_cause)
                if result.status == "passed":
                    # Every public check passed: end the step as if the editor
                    # had sent DONE. The pilot showed a 7B editor rarely sends
                    # DONE and keeps re-checking a finished program until its
                    # turns run out. The hidden tests still decide the score.
                    return finish("done", "checks_passed")
                feedback = self.check_feedback(result)
                checked = (dict(files), feedback)
                note(f"{sent}, then RUN_CHECKS; {check_summary(result)}")
            elif files == before:
                wasted += 1
                feedback = UNCHANGED
                note(f"{sent}; nothing changed")
            else:
                feedback = APPLIED
                note(f"{sent}; applied, no checks run")

    def build_prompt(
        self,
        step: Step,
        files: Program,
        feedback: str,
        history: list[str],
        allowed: list[str],
        turns_left: int,
    ) -> str:
        """The whole prompt for one turn. Its inputs are the current change's
        request, the current files, the last feedback and the turn summaries;
        nothing about private tests or later changes is passed in."""
        n = self.cfg.history_turns
        recent = history[-n:] if n else []
        return self.template.substitute(
            request=step.change.request.strip(),
            files=render_program(dict(files)).strip(),
            feedback=feedback,
            history="\n".join(f"- {line}" for line in recent) if recent else NO_HISTORY,
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


def check_summary(result: CategoryResult) -> str:
    """One line for the turn summaries: the pass count and the first few
    failing checks."""
    if not result.total:
        return "no public check ran (the program may fail to import)"
    text = f"public checks {result.passed} of {result.total} passed"
    failing = [c.node_id.rsplit("::", 1)[-1] for c in result.cases if c.outcome != "passed"]
    if failing:
        more = f" (+{len(failing) - 3} more)" if len(failing) > 3 else ""
        text += "; failing: " + ", ".join(failing[:3]) + more
    return text


def describe_files(before: Program, after: Program, sent: Program) -> str:
    """What a reply sent, for the turn summaries: each file with the lines it
    changed, or that no file was sent."""
    if not sent:
        return "sent no files"
    parts = []
    for path in sorted(sent):
        lines = diff_lines({path: before.get(path, b"")}, {path: after[path]})
        parts.append(f"{path} ({lines} lines changed)" if lines else f"{path} (unchanged)")
    return "sent " + ", ".join(parts)


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


def _cut(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _truncate_middle(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    marker = "\n[... output truncated ...]\n"
    keep = max(0, limit - len(marker))
    return text[: keep // 2] + marker + text[len(text) - (keep - keep // 2) :]
