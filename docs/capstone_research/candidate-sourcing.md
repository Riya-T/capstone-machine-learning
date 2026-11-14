# Sourcing correct starting programs

## Two local writer configurations

On the same 18 prompts and seeds, a direct 14B configuration and an
8B reasoning configuration each produced eight full initial passes.
Four slots passed for both configurations, four passed only for the
direct configuration, four passed only for the reasoning configuration,
and six passed for neither. One reasoning response was malformed.
The configurations also differed in sampling, reasoning and token
limits. The matched roster compares the workflows as operated.
[Matched outcome rows](data/matched-local-writers.json)

## Teacher and public-check sourcing

The neutral teacher used `gpt-6.1-sol` at medium reasoning. Its workspace
was isolated and it saw only the initial requirements and public
examples. The local writer used the pinned Qwen3-8B Q8_0 setup. The
comparison includes the full initial suite, with unambiguous
supplementary cases tested privately.

| Family | Local full passes | Teacher full passes |
| --- | ---: | ---: |
| Calendar Events | 0/4 | 4/4 |
| Document Store | 1/4 | 4/4 |
| Event Bus | 4/4 | 4/4 |
| Feature Flags | 0/4 | 4/4 |
| Party Inventory | 3/4 | 4/4 |
| Warehouse Stock | 0/4 | 4/4 |
| **Total** | **8/24** | **24/24** |

All 16 disagreement outcomes reproduced on the unchanged artifacts.
The two writers used different submission workflows. This comparison
measures the usefulness of the teacher workflow for supplying correct
candidates. Its task sample is small and it supplies no estimate of
natural diversity on arbitrary projects.

In a different six-family experiment, choosing from the same local
drafts using public checks improved the number of correct selections
from 8/24 to 11/24, short of that study's frozen threshold. Public checks
improved selection in some families while also accepting privately
incorrect code. They were useful feedback for a writer to use, and
private tests were still needed to decide correctness.

On two new synthetic tasks, the next neutral teacher batch produced
eight correct starts out of eight. Repair Queue had one executable
group in its four samples and no downstream comparison. Its candidates
all stored a creation-ordered dictionary of job tuples and used the
same lookup, validation, and replacement path. Reward Wallet had two
executable groups among four samples. Shared member lookup versus
per-operation lookup provided a matched comparison under the
selection rule, while the materialized balances and histories were
similar across both groups.

The [structured sourcing evidence](data/sourcing.json) includes the
six-family rows, the local draft-selection summary, group membership,
and the recorded abstentions.
