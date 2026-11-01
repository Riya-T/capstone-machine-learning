# Task families

All 60 task families: their split, where the idea came from, and the
changes each one has. Rules for writing a task are in `README.md`.

The tables are generated from every task's `task.yaml`, so change ids, kinds
and sequences match the tasks exactly. In the Sequences column, `s1` and `s2`
list each sequence's changes in order.

## Status

- All 60 tasks pass task validation (references pass; planted bugs fail
  where declared; each change's tests fail before the change; no leaks).
  This was first run with a local copy of `validate-tasks` that runs pytest
  outside Docker; on 2026-10-26 the real `validate-tasks` passed all 60 in
  the Docker sandbox (`configs/all_tasks.yaml`).
- The writer check (`collect --until initial`, at least 3 of 8 programs
  passing per task and about 5 of 8 on average) was run on the 8 dev tasks
  on 2026-10-26 (`configs/rtx5070_pc.yaml`, Qwen2.5-Coder-7B Q4 in Ollama,
  temperature 0.4). Passing programs out of 8: bank_ledger 8,
  course_enrollment 6, team_roster 4, football_season 3, parking_garage 3,
  lru_cache 3 (only 4 distinct), shopping_cart 3, library_catalog 1;
  average 3.9.
  - shopping_cart was at 0: the spec said "positive integer" but the tests
    reject `1.5` and `"2"`. The spec now says so.
  - library_catalog was at 0. The initial spec dropped the error-order rule
    and non-string borrowers (both now unspecified). It is still at 1:
    7 of 8 programs store loans per book and list them in catalog order,
    not check-out order, failing a public check. It is kept as a hard task
    for now; the team should decide whether to relax the order of
    `get_loans`.
  - With 16 samples per task (the new default; see "Changes from the
    proposal" in the top-level README), passing programs out of 16:
    bank_ledger 15, course_enrollment 11, team_roster 7, lru_cache 7 (only
    8 distinct), football_season 6, shopping_cart 5, parking_garage 4,
    library_catalog 2. With at most 8 going to editing, that is 5.9 per
    task on average, and every dev task but library_catalog has at least 3.
  - The train and eval tasks are being checked in batches of 10; see
    "Writer check" below.
- The dev calibration with the 14B editor (2026-10-31; results in "Changes
  from the proposal" in the top-level README) found two changes whose
  hidden tests disagreed with what the editor was told. Both are fixed:
  - shopping_cart `c_discounts`: the request said reapplying a coupon "must
    not compound" but not whether it raises; 10 of 15 editor attempts
    raised `ValueError`, which the test rejects. The request now says it
    raises nothing.
  - library_catalog `c_reservations`: a hidden test required `ValueError`
    for borrowers `None` and `7`, which the initial spec leaves unspecified
    (since the 2026-10-26 change above); every failed attempt failed only
    on `7`. It now tests only `""`, like the initial tests.

## Writer check

`collect --until initial` (Qwen2.5-Coder-7B Q4, temperature 0.4, 16 samples
per task). A task passes with at least 3 distinct passing programs out of
16. The dev counts are the 16-sample run on `configs/rtx5070_pc.yaml` above.
The eval tasks were run with `configs/noahs_laptop.yaml` in batches of 10
through `configs/writer_check_batch.yaml` (2026-10-28). All 36 train tasks
were run again on 2026-11-01 with `configs/rtx5070_train.yaml`, after the
fixes below; "0 → 7" means the task was fixed after that run and rerun.
Last updated 2026-11-01.

| Task | Split | Passing of 16 | Writer check |
|---|---|---|---|
| `bank_ledger` | dev | 15 | ✅ passed |
| `course_enrollment` | dev | 11 | ✅ passed |
| `team_roster` | dev | 7 | ✅ passed |
| `lru_cache` | dev | 7 | ✅ passed |
| `football_season` | dev | 6 | ✅ passed |
| `shopping_cart` | dev | 5 | ✅ passed |
| `parking_garage` | dev | 4 | ✅ passed |
| `library_catalog` | dev | 2 | ❌ failed |
| `io_meter` | train | 15 | ✅ passed |
| `order_workflow` | train | 15 | ✅ passed |
| `playlist_manager` | train | 15 | ✅ passed |
| `token_bucket` | train | 15 | ✅ passed |
| `budget_envelopes` | train | 14 | ✅ passed |
| `thermostat_zones` | train | 14 | ✅ passed |
| `party_inventory` | train | 13 | ✅ passed |
| `event_bus` | train | 11 | ✅ passed |
| `calendar_events` | train | 10 | ✅ passed |
| `gradebook` | train | 10 | ✅ passed |
| `warehouse_stock` | train | 10 | ✅ passed |
| `high_scores` | train | 1 → 10 | ✅ passed after fix |
| `url_shortener` | train | 0 → 10 | ✅ passed after fix |
| `access_control` | train | 8 | ✅ passed |
| `document_store` | train | 8 | ✅ passed |
| `vending_machine` | train | 0 → 8 (only 8 distinct) | ✅ passed after fix |
| `job_queue` | train | 0 → 7 | ✅ passed after fix |
| `chat_rooms` | train | 6 | ✅ passed |
| `feature_flags` | train | 6 | ✅ passed |
| `gym_memberships` | train | 6 | ✅ passed |
| `clinic_appointments` | train | 4 | ✅ passed |
| `hotel_rooms` | train | 4 | ✅ passed |
| `staff_directory` | train | 4 | ✅ passed |
| `job_board` | train | 3 | ✅ passed (borderline) |
| `hangman_games` | train | 2 | ❌ failed; fixed, not rerun |
| `restaurant_orders` | train | 2 | ❌ failed; fixed, not rerun |
| `recipe_box` | train | 1 | ❌ failed; fixed, not rerun |
| `school_roster` | train | 1 | ❌ failed; fixed, not rerun |
| `iou_tracker` | train | 0 | ❌ failed; fixed, not rerun |
| `login_sessions` | train | 0 | ❌ failed; fixed, not rerun |
| `movie_bookings` | train | 0 | ❌ failed; fixed, not rerun |
| `pantry_inventory` | train | 0 | ❌ failed; fixed, not rerun |
| `ring_buffer` | train | 0 | ❌ failed; fixed, not rerun |
| `robot_fleet` | train | 0 | ❌ failed; fixed, not rerun |
| `stock_portfolio` | train | 0 | ❌ failed; fixed, not rerun |
| `ticket_desk` | train | 0 | ❌ failed; fixed, not rerun |
| `aging_inventory` | eval | 7 | ✅ passed |
| `auction_house` | eval | 5 | ✅ passed |
| `document_versions` | eval | 0 | ❌ failed |
| `elevator_dispatch` | eval | 0 | ❌ failed; redesigned, not rerun |
| `light_grid` | eval | – | not run yet |
| `locker_room` | eval | – | not run yet |
| `meeting_rooms` | eval | – | not run yet |
| `race_telemetry` | eval | – | not run yet |
| `rover_fleet` | eval | – | not run yet |
| `scoreboard` | eval | – | not run yet |
| `seat_reservation` | eval | – | not run yet |
| `social_feed` | eval | – | not run yet |
| `spending_alerts` | eval | – | not run yet |
| `subscription_billing` | eval | – | not run yet |
| `task_board` | eval | – | not run yet |
| `time_clock` | eval | – | not run yet |

So far 33 of the 48 tasks run pass: 7 of 8 dev, 24 of 36 train and 2 of 4
eval. The other 12 eval tasks have not been run yet. Data collection started
on the 24 train tasks that pass (2026-11-01). The 12 that fail have been
fixed (see "Fixed on 2026-11-01, not rerun yet" below) and are rerun once
that collection is done, since the writer and the editor share the GPU.

What the writer kept getting wrong, and the fixes that worked:

- **Error order between `KeyError` and `ValueError`.** The writer
  validates every argument before looking anything up, so a rule like
  "a missing id is reported before a bad value" failed in nearly every
  program even with a public check for it. Such rules were made
  unspecified and their hidden tests removed (`chat_rooms`,
  `document_store`, `document_versions`, `event_bus`, `hotel_rooms`,
  `gym_memberships`, `feature_flags`, and on 2026-11-01 `vending_machine`
  and `high_scores`). The same goes for `get_latest_score` on a player who
  is not on the board (`high_scores`): 12 of 15 programs raised the "no
  scores" `ScoreError` instead of `KeyError`; either is now allowed.
- **Non-string values.** The writer checks `if not name`, which lets `7`
  through. `7` was removed from the invalid bidders (`auction_house`),
  patients (`clinic_appointments`), titles (`job_board`) and codes and
  targets (`url_shortener`, which now says "an empty string or `None`");
  `""` and `None` are still tested. Where a non-string id must raise
  `KeyError`, saying "it counts as unknown: `KeyError`, not `ValueError`"
  worked (`chat_rooms`).
- **`True` as a number.** `isinstance(True, int)` holds, and every
  `job_queue` program accepted `True` as a priority although the spec said
  "not a `bool`". `bool` priorities are now unspecified, as `bool` values
  already were in most tasks.
- **Lists kept up to date by hand.** A list of allowed clients or wilted
  batches that is appended to when things change comes out in the wrong
  order. Describing it as "the same ids as `get_…()`, in the same order,
  keeping only …" fixed `access_control` and `aging_inventory`.
- **Two-part rules.** Restating "first bid vs. later bids" as one minimum
  bid fixed `auction_house`. Worked examples in the spec helped more than
  extra public checks, which the writer often ignores.
- **Tests that contradicted their own spec.** `job_board` rejected a `True`
  salary, which the spec lists as unspecified; `feature_flags` matched on an
  error message's text. Both tests were fixed.

On review (2026-11-01), four sentences added by these fixes were taken out
again, because a spec should say what the program does, not how to build
it (how the writer structures the code is what the project measures), and
one was wrong:

- `iou_tracker`: "sorting with `reverse=True` is wrong (it reverses the
  ties too)". Python's sort is stable with `reverse=True`: equal amounts
  keep their order. The worked example stays.
- `aging_inventory`: "a list of wilted ids built up in `end_day` gets this
  wrong ... so work it out from the batches".
- `document_versions`: "so keep the count of revisions written separately
  from the revisions kept".
- `elevator_dispatch`: that the record behind `get_destination` is what
  makes a repeated call raise, and that riders keep their destination "so
  the car knows where each rider gets out".

Fixed on 2026-11-01, not rerun yet. "Stored" is how many of the 16 stored
programs pass the edited tests; fixes to the wording only show once the
writer is sampled again.

- **More input checks made unspecified**, as above:
  - `7` as a name or symbol: `login_sessions`, `movie_bookings` (customers),
    `recipe_box`, `stock_portfolio`, including the `c_profit` and
    `c_sectors` tests, whose requests point back to the usual symbol rules.
  - Numbers that are not `int`s, such as `1.5`, `"10"` or `None`; 0 and
    negatives are still tested. Most programs only check `<= 0`: 14 of 15
    in `stock_portfolio`, 12 of 15 capacities in `ring_buffer`, 10 of 15
    in `restaurant_orders`.
  - Headings that are not a single letter (`""`, `"NE"`, `None`) and `None`
    as the commands in `robot_fleet` (also in the `c_distance` test). All
    16 programs test `heading not in "NESW"`, which accepts `""` and `"NE"`.
  - `True` as a start or seat count in `movie_bookings`; the spec already
    listed `bool` values as unspecified, so those tests contradicted it.
  - Error order between `KeyError` and `ValueError`: `movie_bookings`
    (`book`), `recipe_box` (`add_ingredient`).
  - The order of users with equal amounts in `iou_tracker`. The worked
    example for it had not helped (0 of 16). `c_net_query` keeps its own
    tie rule for its new methods.
- **Behavior the writer got wrong, now stated more plainly with examples**
  (no tests removed):
  - `login_sessions`: all 11 programs treated "registered" as "has signed
    in", so a registered user who never signed in raised `KeyError`. The
    spec now says a user is known from registration on, what signing out
    leaves, and describes `get_signed_in` like `access_control`'s list.
  - `school_roster`: 15 of 16 checked names against the grades. The spec
    now says it keeps each student's grade, with examples.
  - `hangman_games`: 14 of 16 kept accepting guesses after a win; the rule
    now has its own bullet and an example.
  - `recipe_box`: 11 of 14 never added up a repeated ingredient; "a recipe
    lists each ingredient once" plus examples for both lists.
  - `pantry_inventory`: no program sorted batches by use-by day, and the
    public checks only ever added them in order. The spec now says batches
    come in any order, with an example, and one public check adds a batch
    out of order. It also says a used-up batch is gone and that a shortage
    takes nothing.
  - `ticket_desk`: 14 of 16 never set the status to `"assigned"`; queues
    now use the "same ids as `get_tickets()`" wording.
  - `movie_bookings`: no program sorted showings by start; reworded with an
    example. The sort stays: the s2 regression bug depends on it.
  - `iou_tracker`: 5 programs read `get_owed_to(alice)` as what alice owes;
    both methods now have an example.
  - `ring_buffer`: 11 of 15 wrap the read position wrongly; an example with
    capacity 2 was added.
  - `robot_fleet`: 9 of 16 accepted only `"L"` and `"R"`. The spec now names
    the three letters in the validation rule, with `"X"` as an example.
  - `stock_portfolio`: 12 of 15 did not check the symbol in `get_shares`;
    the rule is now repeated there.
- `stock_portfolio`'s planted bug `v0_cash_checked_before_price` could only
  be caught with a non-`int` price, so it became
  `v0_held_checked_before_price` (`sell` checks the shares held before the
  price).
- Stored programs passing the edited tests: `restaurant_orders` 12,
  `ring_buffer` 4, `stock_portfolio` 3, `robot_fleet` 3, `recipe_box` 3,
  `iou_tracker` 2, `hangman_games` 2, `school_roster` 1, the rest 0. If a
  rerun still fails, `recipe_box` (it returns lists of tuples) and
  `iou_tracker` (method names that read both ways) may need a redesign:
  a team decision.

Still open:

- `document_versions`: every near-miss fails only the 5-revision cap (drop
  the oldest kept revision, keep the numbering and the count). Moving the
  cap from the initial spec into `c_retention` would fix it, but
  `c_search`, `c_restore` and `c_version_check` all define behavior for
  revisions no longer kept, and `c_search` runs before `c_retention` in
  s2, so that is a rewrite of the task's changes. Needs a team decision.
- `elevator_dispatch`: programs skipped the stop when a car was moved to
  the floor it was already on. That case is now unspecified: its public
  check is gone, and the 9 tests that relied on it (2 initial, plus some in
  `c_capacity`, `c_service`, `c_wait` and `c_cancel`) were rewritten, most
  of them to load cars on floor 1 instead of floor 0. A new
  `get_destination` method makes the writer keep each passenger's
  destination. Needs a rerun (`configs/writer_check_redo.yaml`).
- `access_control` lost the planted bug `v0_allowed_in_allow_order`: a
  public check now covers that order, so the bug could no longer pass the
  public checks. `v0_access_before_message` still covers the initial spec.

## How the families were chosen

- **Every task is a stateful single class with a small interface** and at
  least two natural internal designs (store the current value vs. derive it
  from a history; validation inline vs. centralized; records vs. an event
  log). The later changes are chosen to punish one of those designs, because
  that is where editor success depends on the writer's design.
- **Sources are idea quarries, not text.** Nothing was copied from any
  source: not spec text, not tests, not solutions. A source gave the domain,
  the list of behaviors and the edge cases; each task was written from
  scratch to the README rules.
  - *ClassEval* (MIT): stateful classes from its class-level benchmark.
  - *Exercism* (MIT): stateful practice exercises.
  - *Katas* (kata-log, Unlicense; Emily Bache's katas, MIT): used only for
    the **shape of the eval change sequences**, since kata steps are designed
    to expose rigid designs. Names, wording and numbers are our own, and the
    famous one (Gilded Rose) is fully re-skinned.
  - *Libraries*: the feature-request histories of small Python libraries
    (cachetools, schedule, transitions, pyee, ...) as realistic later changes.
  - *Original*: written by the team.
- **Splits.** Train and dev families may come from any source. Eval families
  are original domains whose change sequences follow a kata's shape. The
  eval-only change kinds (`configuration`, `concurrency_control`) never
  appear in train or dev, and every eval sequence has at least one of them.
- **Close variants stay in one split**: e.g. `robot_fleet` (train) and
  `rover_fleet` (eval) were written to differ in grid, commands and
  interface; `document_store` / `document_versions` and `calendar_events` /
  `meeting_rooms` likewise.

## Change kinds used

| Kind | Train | Dev | Eval |
|---|---|---|---|
| `undo` | 20 | 4 | 11 |
| `state_flag` | 19 | 5 | 8 |
| `derived_value` | 21 | 5 | 6 |
| `validation_rule` | 14 | 6 | 1 |
| `query` | 15 | 1 | 5 |
| `grouping` | 13 | 1 | 5 |
| `configuration` | 0 | 0 | 16 |
| `concurrency_control` | 0 | 0 | 12 |
| `atomic_operation` | 6 | 2 | 0 |
| **total** | 108 | 24 | 64 |

## Dev (8)

| Task | Module | Source | Idea | Changes | Sequences |
|---|---|---|---|---|---|
| `bank_ledger` | `ledger.py` | original | accounts, deposits, withdrawals, transfers and a history of movements | `c_overdraft` validation_rule: overdraft limits<br>`c_fees` derived_value: fee on money leaving an account<br>`c_freeze` state_flag: frozen accounts | s1: overdraft → fees<br>s2: freeze → overdraft |
| `course_enrollment` | `enrollment.py` | original (rewritten) | courses with a capacity, students, rosters and schedules | `c_prerequisites` validation_rule: prerequisites, completed courses<br>`c_waitlist` undo: drop a course, waitlist promotion<br>`c_freeze` state_flag: frozen courses | s1: prerequisites → waitlist<br>s2: freeze → prerequisites |
| `football_season` | `season.py` | original | games, win/loss/tie records, standings | `c_remove` undo: remove a recorded game<br>`c_divisions` grouping: divisions<br>`c_streak` derived_value: current streak | s1: remove → divisions<br>s2: streak → remove |
| `library_catalog` | `library.py` | original (rewritten) | books by ISBN with copies, check-outs, returns, history | `c_one_copy` validation_rule: one copy of a book per borrower<br>`c_reservations` atomic_operation: reservation queue, hand-over on return<br>`c_loan_log` query: loan log filtered by borrower or book | s1: one_copy → reservations<br>s2: loan_log → one_copy |
| `lru_cache` | `cache.py` | library: cachetools | fixed-capacity cache, least-recently-used eviction | `c_stats` derived_value: hits, misses, evictions<br>`c_pin` state_flag: pinned entries<br>`c_remove` undo: remove a key, clear by prefix | s1: stats → pin<br>s2: remove → stats |
| `parking_garage` | `garage.py` | original | levels, vehicles entering and leaving, minutes parked | `c_sizes` validation_rule: vehicle and level sizes<br>`c_report` derived_value: per-level usage report, peak<br>`c_reserve` state_flag: reserved spots | s1: sizes → report<br>s2: reserve → sizes |
| `shopping_cart` | `cart.py` | original | items, quantities, prices and the cart total | `c_inventory` validation_rule: stock limits<br>`c_discounts` derived_value: coupon discounts<br>`c_undo` undo: undo the last add or remove | seq_cart_workflow_1: inventory → discounts<br>seq_cart_workflow_2: discounts → undo |
| `team_roster` | `roster.py` | original | a basketball roster under a salary cap | `c_trades` atomic_operation: trades in one step<br>`c_position_limits` validation_rule: players per position<br>`c_injuries` state_flag: injured list | s1: trades → position_limits<br>s2: injuries → trades |

## Train (36)

| Task | Module | Source | Idea | Changes | Sequences |
|---|---|---|---|---|---|
| `access_control` | `gateway.py` | ClassEval Server | gateway clients, an allow list, messages | `c_ban` state_flag: banned clients<br>`c_groups` grouping: client groups<br>`c_counts` derived_value: message counts, ranking | s1: ban → groups<br>s2: counts → ban |
| `budget_envelopes` | `envelopes.py` | budgeting apps (envelope method) | income, envelopes, allocating and spending | `c_move` atomic_operation: move money, allocate many at once<br>`c_totals` derived_value: spending totals<br>`c_lock` state_flag: locked envelopes | s1: move → totals<br>s2: lock → move |
| `calendar_events` | `agenda.py` | ClassEval CalendarUtil | one day's events by minute, attendees, schedules | `c_no_overlap` validation_rule: no double-booking<br>`c_cancel` undo: cancel events, remove attendees<br>`c_free_busy` query: free/busy over a window | s1: no_overlap → cancel<br>s2: free_busy → no_overlap |
| `chat_rooms` | `chat.py` | ClassEval Chat | users, rooms joined on first use, messages | `c_mute` state_flag: muted users<br>`c_search` query: filter messages, a user's posts<br>`c_delete` undo: message ids, delete a message | s1: mute → search<br>s2: delete → mute |
| `clinic_appointments` | `clinic.py` | original | doctors, open slots, patient bookings | `c_cancel` undo: cancel bookings, close slots<br>`c_double_booking` validation_rule: no patient double-booking<br>`c_daily_load` derived_value: daily load per doctor | s1: cancel → double_booking<br>s2: daily_load → cancel |
| `document_store` | `docstore.py` | library: tinydb | documents with titles, bodies and tags | `c_tag_groups` grouping: tag groups<br>`c_search` query: text search<br>`c_trash` undo: trash and restore | s1: tag_groups → search<br>s2: trash → tag_groups |
| `event_bus` | `bus.py` | library: pyee | topics, subscribers, publishing, deliveries | `c_unsubscribe` undo: unsubscribe<br>`c_groups` grouping: topic groups<br>`c_counts` derived_value: delivery and publish counts | s1: unsubscribe → groups<br>s2: counts → unsubscribe |
| `feature_flags` | `flags.py` | library: flipper | flags, percentage rollouts, per-user switches | `c_groups` grouping: user groups<br>`c_kill_switch` state_flag: kill switch<br>`c_audit` query: change audit | s1: groups → kill_switch<br>s2: audit → groups |
| `gradebook` | `gradebook.py` | ClassEval AssessmentSystem | students, assignments, scores and totals | `c_late` state_flag: late submissions earn half<br>`c_ranking` query: class and assignment rankings<br>`c_drop_lowest` derived_value: totals without the lowest scores | s1: late → ranking<br>s2: drop_lowest → late |
| `gym_memberships` | `gym.py` | original | plans, members, check-ins by day | `c_freeze` state_flag: frozen memberships<br>`c_visits` derived_value: visit counts per member and plan<br>`c_tiers` grouping: plan tiers | s1: freeze → visits<br>s2: tiers → freeze |
| `hangman_games` | `hangman.py` | Exercism hangman | several hangman games, guesses, progress | `c_max_wrong` validation_rule: wrong-guess limit, lost games<br>`c_hint` derived_value: hints<br>`c_take_back` undo: take back the last guess | s1: max_wrong → hint<br>s2: take_back → max_wrong |
| `high_scores` | `scores.py` | Exercism high-scores | players, recorded scores, top scores | `c_best` derived_value: personal bests, leaderboard<br>`c_seasons` grouping: seasons<br>`c_remove` undo: remove a score, undo the last | s1: best → seasons<br>s2: remove → best |
| `hotel_rooms` | `hotel.py` | ClassEval Hotel | rooms, bookings by night, check-in and check-out | `c_cancel` undo: cancel a booking<br>`c_categories` grouping: room categories, book any of a category<br>`c_occupancy` derived_value: occupancy figures | s1: cancel → categories<br>s2: occupancy → cancel |
| `io_meter` | `meter.py` | Exercism paasio | streams, bytes read and written, operation counts | `c_quota` validation_rule: per-stream quotas<br>`c_pause` state_flag: paused streams<br>`c_totals` derived_value: totals, largest op, busiest stream | s1: quota → pause<br>s2: totals → quota |
| `iou_tracker` | `ious.py` | Exercism rest-api | who owes whom, IOU history | `c_settle` atomic_operation: pay several lenders all or nothing<br>`c_net_query` query: net amounts, debtors, creditors<br>`c_forgive` undo: forgive the latest IOU | s1: settle → net_query<br>s2: forgive → settle |
| `job_board` | `board.py` | ClassEval JobMarketplace | jobs with salaries, applicants, applications | `c_close` state_flag: close and reopen jobs<br>`c_search` query: find jobs, jobs by popularity<br>`c_limit` validation_rule: per-applicant and per-job limits | s1: close → search<br>s2: limit → close |
| `job_queue` | `jobs.py` | library: schedule | jobs with priorities and dependencies | `c_deprules` validation_rule: add dependencies, no cycles<br>`c_pause` state_flag: paused jobs<br>`c_cancel` undo: cancel a job | s1: deprules → pause<br>s2: cancel → deprules |
| `login_sessions` | `sessions.py` | ClassEval SignInSystem | registered users, sign in and out, who is signed in | `c_lockout` state_flag: lock after 3 wrong passwords<br>`c_capacity` validation_rule: max users signed in<br>`c_activity` query: activity log, users by activity | s1: lockout → capacity<br>s2: activity → lockout |
| `movie_bookings` | `bookings.py` | ClassEval MovieBookingSystem | movies, showings with seats, bookings | `c_cancel` undo: cancel a booking<br>`c_genres` grouping: genres<br>`c_search` query: find showings and a customer's bookings | s1: cancel → genres<br>s2: search → cancel |
| `order_workflow` | `workflow.py` | library: transitions | orders moving through five states | `c_history` query: state history<br>`c_guards` validation_rule: payment and address guards (opt-in)<br>`c_rollback` undo: roll back a move | s1: history → guards<br>s2: rollback → history |
| `pantry_inventory` | `pantry.py` | Exercism inventory-management | food items in batches with use-by days | `c_expired` state_flag: current day, expired batches<br>`c_categories` grouping: categories<br>`c_shopping_list` derived_value: minimums and a shopping list | s1: expired → categories<br>s2: shopping_list → expired |
| `party_inventory` | `party.py` | ClassEval RPGCharacter | characters, items in bags, equipping | `c_carry_limit` validation_rule: carry weight vs. strength<br>`c_trade` atomic_operation: swap two items in one step<br>`c_status` state_flag: stunned and petrified | s1: carry_limit → trade<br>s2: status → carry_limit |
| `playlist_manager` | `playlist.py` | ClassEval MusicPlayer | songs, playlists, a play queue | `c_remove` undo: remove from a playlist or the library<br>`c_duration` derived_value: durations, time played<br>`c_by_artist` query: search by artist | s1: remove → duration<br>s2: by_artist → remove |
| `recipe_box` | `recipes.py` | original | recipes, ingredients, servings, shopping lists | `c_pantry` derived_value: pantry, missing items, cook<br>`c_categories` grouping: categories<br>`c_remove` undo: remove ingredient, undo last add | s1: pantry → categories<br>s2: remove → pantry |
| `restaurant_orders` | `orders.py` | ClassEval Order | menu, open tables, orders, bills | `c_void` undo: void the last order call<br>`c_courses` grouping: courses<br>`c_service` derived_value: service charge, takings | s1: void → courses<br>s2: service → void |
| `ring_buffer` | `ring_buffer.py` | Exercism circular-buffer | bounded first-in first-out buffer | `c_overwrite` state_flag: overwrite mode<br>`c_counts` derived_value: written, read, discarded totals<br>`c_peek` query: peek, newest, contents | s1: overwrite → counts<br>s2: peek → overwrite |
| `robot_fleet` | `fleet.py` | Exercism robot-simulator | robots on an unbounded grid, L/R/A commands | `c_bounds` validation_rule: grid bounds<br>`c_disabled` state_flag: disabled robots<br>`c_distance` derived_value: distance, displacement, cells visited | s1: bounds → disabled<br>s2: distance → bounds |
| `school_roster` | `roster.py` | Exercism grade-school | students by grade 1-12 | `c_move` atomic_operation: move several students, grade cap<br>`c_homeroom` grouping: homerooms<br>`c_withdraw` undo: withdraw and reinstate | s1: move → homeroom<br>s2: withdraw → move |
| `staff_directory` | `directory.py` | ClassEval HRManagementSystem | departments, employees, salaries | `c_leave` state_flag: employees on leave<br>`c_payroll` derived_value: payroll, salary history<br>`c_transfer` atomic_operation: headcount caps, multi-employee transfer | s1: leave → payroll<br>s2: transfer → leave |
| `stock_portfolio` | `portfolio.py` | ClassEval StockPortfolioTracker | cash, buying and selling shares, holdings, trades | `c_sectors` grouping: sectors<br>`c_profit` derived_value: FIFO realized profit, cost basis<br>`c_undo` undo: cancel the last trade | s1: sectors → profit<br>s2: undo → sectors |
| `thermostat_zones` | `thermostat.py` | ClassEval Thermostat | zones with a mode, a target and readings | `c_limits` validation_rule: per-zone target limits<br>`c_hold` state_flag: zones on hold<br>`c_demand` derived_value: heating and cooling demand | s1: limits → hold<br>s2: demand → limits |
| `ticket_desk` | `desk.py` | original | support tickets, agents, assignment, resolution | `c_reopen` undo: reopen a ticket<br>`c_priority` query: queues by status and priority<br>`c_limit` validation_rule: per-agent limit | s1: reopen → priority<br>s2: limit → reopen |
| `token_bucket` | `limiter.py` | library: pyrate-limiter | clients, requests per fixed window, explicit ticks | `c_block` state_flag: blocked clients<br>`c_usage` query: request times, usage over a range<br>`c_refund` undo: refund a request by receipt | s1: block → usage<br>s2: refund → block |
| `url_shortener` | `shortener.py` | library: pyshorteners | short codes, targets, hit counts | `c_disable` state_flag: disabled links<br>`c_stats` derived_value: hit statistics per target<br>`c_alias` validation_rule: code rules, case-insensitive, reserved codes | s1: disable → stats<br>s2: alias → disable |
| `vending_machine` | `vending.py` | ClassEval VendingMachine | slots, prices, coins, purchases, change | `c_capacity` validation_rule: slot capacity<br>`c_sales` derived_value: sales and revenue report<br>`c_outage` state_flag: slots out of order | s1: capacity → sales<br>s2: outage → capacity |
| `warehouse_stock` | `warehouse.py` | ClassEval Warehouse | products, receiving stock, orders, a stock history | `c_returns` undo: return an order<br>`c_bundle` atomic_operation: several products all or nothing<br>`c_lowstock` query: low stock, orders by product, large orders | s1: returns → bundle<br>s2: lowstock → returns |

## Eval (16)

Four changes each, two sequences of three. Kata shape names the kata whose change pattern the sequence follows; the domain and every word are our own.

| Task | Module | Kata shape | Idea | Changes | Sequences |
|---|---|---|---|---|---|
| `aging_inventory` | `cooler.py` | Gilded Rose, fully re-skinned | cut-flower batches losing freshness each day | `c_loss_rates` configuration: loss rates per cooler and batch<br>`c_categories` grouping: categories with their own rates<br>`c_hold` state_flag: batches on hold<br>`c_undo_day` undo: undo the last day | s1: loss_rates → categories → hold<br>s2: undo_day → loss_rates → categories |
| `auction_house` | `auction.py` | none (original) | lots, bids with a minimum raise of 10 | `c_increment` configuration: minimum raise per house and lot<br>`c_bid_version` concurrency_control: lot versions<br>`c_withdraw` undo: withdraw a bidder's bids<br>`c_closing` state_flag: close lots, winners | s1: increment → bid_version → withdraw<br>s2: closing → increment → bid_version |
| `document_versions` | `wiki.py` | none (original) | wiki pages with numbered revisions, last 5 readable | `c_version_check` concurrency_control: page versions<br>`c_retention` configuration: revisions kept per wiki and page<br>`c_restore` undo: roll back to a revision<br>`c_search` query: find pages, contributions | s1: version_check → retention → restore<br>s2: search → version_check → retention |
| `elevator_dispatch` | `elevators.py` | Lift | floors, cars, calls, riders getting in and out | `c_capacity` configuration: car capacity per building and car<br>`c_service` state_flag: cars out of service<br>`c_wait` derived_value: wait statistics<br>`c_cancel` undo: cancel a call | s1: capacity → service → wait<br>s2: cancel → capacity → service |
| `light_grid` | `lights.py` | Christmas Lights | on/off/toggle over rectangles of a light grid | `c_brightness` configuration: brightness levels, adjustable maximum<br>`c_locks` state_flag: locked regions<br>`c_undo` undo: undo commands<br>`c_count_query` query: counts over rectangles | s1: brightness → locks → undo<br>s2: count_query → brightness → locks |
| `locker_room` | `lockers.py` | Configure Wardrobe | lockers of fixed sizes and fees, storing items | `c_size_table` configuration: size and fee table<br>`c_out_of_order` state_flag: lockers out of order<br>`c_undo` undo: undo the last store or retrieve<br>`c_versions` concurrency_control: locker versions, move items | s1: size_table → out_of_order → undo<br>s2: versions → size_table → out_of_order |
| `meeting_rooms` | `rooms.py` | none (original) | rooms booked by the minute with a 10-minute gap | `c_buffer` configuration: gap per planner and room<br>`c_booking_versions` concurrency_control: booking versions<br>`c_cancel` undo: cancel a booking<br>`c_usage` derived_value: booked minutes, usage ranking | s1: buffer → booking_versions → cancel<br>s2: usage → buffer → booking_versions |
| `race_telemetry` | `telemetry.py` | Race Car | cars, races, lap times, results, a points table | `c_points_table` configuration: points table per series and race<br>`c_penalties` derived_value: time penalties<br>`c_car_classes` grouping: car classes<br>`c_lap_corrections` concurrency_control: versioned lap corrections | s1: points_table → penalties → car_classes<br>s2: lap_corrections → points_table → penalties |
| `rover_fleet` | `rovers.py` | Mars Rover | rovers on a wrapping 10x10 plateau, F/B/L/R commands | `c_grid_size` configuration: plateau size, wrapping on/off<br>`c_obstacles` validation_rule: obstacles<br>`c_paths` query: paths, visitors, explored cells<br>`c_versioned_commands` concurrency_control: rover versions | s1: grid_size → obstacles → paths<br>s2: versioned_commands → grid_size → obstacles |
| `scoreboard` | `scoreboard.py` | Score Keeper | one match, scoring events with fixed point values | `c_points` configuration: adjustable point values<br>`c_corrections` undo: undo scoring events<br>`c_periods` grouping: periods<br>`c_versions` concurrency_control: team versions | s1: points → corrections → periods<br>s2: versions → points → corrections |
| `seat_reservation` | `seats.py` | Train Reservation | groups booked onto coaches under a 70% fill rule | `c_fill_percent` configuration: fill rule per planner and coach<br>`c_cancel` undo: full and partial cancellation<br>`c_coach_groups` grouping: coach groups<br>`c_versions` concurrency_control: booking versions, add seats | s1: fill_percent → cancel → coach_groups<br>s2: versions → fill_percent → cancel |
| `social_feed` | `feed.py` | Social Network | users, posts up to 280 characters, follows, timelines | `c_post_limit` configuration: post length limit per feed and user<br>`c_block` state_flag: blocking<br>`c_mentions` query: @mentions<br>`c_edits` concurrency_control: edits with post versions | s1: post_limit → block → mentions<br>s2: edits → post_limit → block |
| `spending_alerts` | `spending.py` | Unusual Spending | payments by account, month and category, alerts | `c_thresholds` configuration: alert thresholds per tracker and category<br>`c_refunds` undo: full and partial refunds<br>`c_groups` grouping: category groups<br>`c_month_compare` derived_value: month-on-month comparison | s1: thresholds → refunds → groups<br>s2: month_compare → thresholds → refunds |
| `subscription_billing` | `billing.py` | none (original) | plans, subscribers, billing cycles, upgrades | `c_proration` configuration: upgrade charge percentage per system and plan<br>`c_pause` state_flag: paused subscriptions<br>`c_plan_version` concurrency_control: subscription versions<br>`c_revenue` derived_value: revenue per plan | s1: proration → pause → plan_version<br>s2: revenue → proration → pause |
| `task_board` | `board.py` | Task List | projects, tasks with due days, an open-task limit | `c_open_limit` configuration: open-task limit per board and project<br>`c_versions` concurrency_control: task versions, rename, set due day<br>`c_archive` undo: archive and restore<br>`c_overdue` query: overdue and due-on queries | s1: open_limit → versions → archive<br>s2: overdue → open_limit → versions |
| `time_clock` | `timeclock.py` | Clock-In | employees clocking in and out, worked and overtime minutes | `c_overtime_rules` configuration: overtime threshold per clock and employee<br>`c_versions` concurrency_control: versioned shift corrections<br>`c_breaks` derived_value: unpaid breaks<br>`c_approval` state_flag: approved shifts | s1: overtime_rules → versions → breaks<br>s2: approval → overtime_rules → versions |
