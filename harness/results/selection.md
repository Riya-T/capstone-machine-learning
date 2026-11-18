Held-out gain of picking the best of k programs by one sequence, scored on
the other (changes per sequence, against a program picked at random):

| Writer | Average program | Best of 2, probe 1 rep | Best of 2, probe 3 reps | Best of 4, probe 1 rep | Best of 4, probe 3 reps | Best of 8, probe 1 rep | Best of 8, probe 3 reps |
|---|---:|---:|---:|---:|---:|---:|---:|
| base | 1.43 | +0.06 (+0.01 to +0.12) | +0.09 (+0.01 to +0.18) | +0.09 (+0.02 to +0.18) | +0.17 (+0.04 to +0.32) | +0.11 (+0.03 to +0.19) | +0.27 (+0.10 to +0.45) |
| prompt | 1.43 | +0.00 (-0.05 to +0.07) | -0.02 (-0.10 to +0.06) | -0.01 (-0.08 to +0.08) | -0.09 (-0.22 to +0.03) | -0.02 (-0.10 to +0.07) | -0.16 (-0.32 to -0.00) |
| dpo3 | 1.45 | +0.02 (-0.02 to +0.05) | +0.05 (-0.03 to +0.13) | +0.01 (-0.05 to +0.07) | +0.05 (-0.08 to +0.16) | +0.01 (-0.08 to +0.08) | +0.03 (-0.12 to +0.18) |
| radon | 1.35 | +0.05 (-0.02 to +0.14) | +0.08 (-0.02 to +0.18) | +0.05 (-0.05 to +0.16) | +0.12 (-0.03 to +0.26) | +0.07 (-0.05 to +0.18) | +0.15 (-0.03 to +0.30) |
| sft | 1.47 | +0.02 (-0.01 to +0.05) | +0.05 (-0.02 to +0.11) | +0.05 (-0.01 to +0.11) | +0.09 (-0.05 to +0.24) | +0.05 (-0.01 to +0.11) | +0.05 (-0.13 to +0.22) |
| Mean over the 5 writers | | +0.03 (+0.00 to +0.07) | +0.05 (+0.01 to +0.10) | +0.04 (+0.00 to +0.09) | +0.07 (-0.00 to +0.15) | +0.04 (-0.00 to +0.10) | +0.07 (-0.02 to +0.16) |

Per task, best of 8 with a 3-repetition probe (tasks with fewer programs
use all of them):

| Writer | Tasks up / down / same | Without the task with the largest gain | Largest gains |
|---|---:|---:|---|
| base | 12 / 2 / 2 | +0.21 (+0.07 to +0.36) | race_telemetry +1.13, time_clock +0.81, rover_fleet +0.64 |
| prompt | 4 / 9 / 3 | -0.19 (-0.35 to -0.03) | light_grid +0.33, locker_room +0.33, task_board +0.22 |
| dpo3 | 8 / 6 / 2 | +0.00 (-0.15 to +0.15) | seat_reservation +0.50, rover_fleet +0.47, light_grid +0.40 |
| radon | 9 / 4 / 3 | +0.11 (-0.06 to +0.27) | meeting_rooms +0.67, light_grid +0.58, rover_fleet +0.52 |
| sft | 7 / 6 / 3 | -0.01 (-0.16 to +0.14) | rover_fleet +0.88, locker_room +0.53, task_board +0.42 |
