# V32 fixed-development counterfactual diagnosis

## Disposition

`FAIL_GATE`; 13/20 versus the pre-registered requirement of at least 16/20.
V32 from-scratch training is prohibited and the locked-test manifest remains
unread.

All 13 v31 successes and their complete telemetry trajectories are exactly
preserved. The prior collision scenario 0003 is also exact. The four prior
phase-9 timeouts (0005, 0008, 0013, 0017) instead collide in phase 8 with
`front_right_bot` after only 4, 26, 29, and 7 recorded exact-bound speed rows.
They never reach phase 9. Existing collision scenarios 0006/0019 receive
6/4 speed rows; all seven failures end with `[TOP,TOP,AIR,TOP]`.

The exact-bound phase-8 sign moves axle yaw in the registered direction at
matched time, but is dynamically too aggressive. Detailed immutable evidence
and the next bracket are in
`runs/diagnostics/v32_phase8_9_bound_counter_yaw_postrun_analysis.json`.

