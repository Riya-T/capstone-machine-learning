# Review proposal for the preference-label testbed

## Decision under review

Test whether a starting-program advantage persists across different
requests before using it as a training label. This small controlled
study isolates two known starting programs from the team's sampled
writer output. It complements the team's stored-run diagnostics with
new matched editor attempts and test-level correctness checks.

The November 13 diagnostics estimate that about 4% of within-task trial
variance belongs to the program on the present training tasks. Cross-
sequence winner agreement was 58% among comparisons where both
sequences had a winner. The controlled pilot asks a narrower question
under another editor configuration. Do two specific, correct designs
exhibit a repeatable difference on two requests that both exercise the
same state invariant? The estimates from the two studies refer to
different populations and are kept separate.
[Team diagnostics](../../harness/results/diagnostics.md)

## Testbed requirements for the next collection

1. Use task families with interacting state and real freedom to choose a
   design. Certify each starting implementation and document why the
   proposed change touches that design. A pair of small controlled
   implementations can validate the measurement pipeline before new
   sampled data is collected.
2. Define precisely what an invalid call does. Write at least one
   public example for each requested change. Keep wider state and
   error cases private. A reference must pass and a deliberately
   incorrect implementation must fail each critical behavior. Require
   both existing and new feature tests for a pass.
3. Use independent contexts and counterbalance starting programs
   within matched seeds. Save the actual artifact and stop reason.
   Report private behavioral failures and unscored submissions
   separately. Compare rankings on separate requests after the full
   roster completes.
4. Leave the pair unlabeled if the direction changes, if both
   designs saturate on an essential request, or if a correctness
   gap drives the result. Reuse the team's cross-sequence headroom and
   variance diagnostics on a larger candidate population. Treat each
   task as a group. Check label stability before training on the
   collected data.

This folder describes a research pilot. It adds no new training data,
changes no existing benchmark contract, and affects no training or
evaluation command. Full raw generations and replay logs are retained
in an independently verified local archive. Reviewable compact outcome
and provenance records accompany the result.
