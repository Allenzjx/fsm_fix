# V33 fixed-development counterfactual diagnosis

`DEVELOPMENT_IDEAL_NOT_REACHED`; 13/20.

V33 preserves all 13 v31 successes exactly but ends with six body/link
collisions and one phase-9 timeout. Moderate phase-8 speed lets scenario 0008
survive through all 162 phase-8 correction rows and improves its terminal yaw
by 0.01935 rad relative to v31, but it still times out after 631 phase-9
exact-bound rows. Scenarios 0005/0013/0017 still collide in phase 8.

Because v31/v32/v33 tie on success and v31 has only three collisions versus
seven/six, the phase-9-only v31 behavior is selected for formal B/C training.
The unmet ideal development target will be disclosed; it is not relabeled as
a pass.

Full evidence:
`runs/diagnostics/v33_phase8_moderate_phase9_bound_counter_yaw_postrun_analysis.json`.

