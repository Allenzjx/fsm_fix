# Method B reward-v3 seed-11 50 mm smoke attempt002

- Status: `SMOKE_PASS`; audit acceptance `PASS`.
- Real IsaacLab checks passed in 16 environments: finite 96-D Actor
  observations, finite 146-D Critic states/values, finite bounded 12-D policy
  samples, finite contacts, exact zero-residual FSM equivalence, and an
  explicit finite two-environment partial reset.
- Direct effective residual-bound provenance:
  - wheel-center x: 0.015 m;
  - wheel-center z: 0.020 m;
  - wheel speed: 0.20 rad/s.
- Direct effective reward provenance includes
  `residual_magnitude=-0.5` and
  `residual_left_right_asymmetry=-1.0`.
- Common config SHA-256:
  `337defd27f0020a0d45dd47e13ea774be42ae25d9998c333a2ace675c6c2a50f`.
- Training-result SHA-256:
  `bd8c14341a6834b6cd48ccf19224d8af1381794025a2e46a8e9a034a9814e400`.

This smoke contributes zero optimization transitions. It authorizes one
from-scratch full-budget Method-B reward-v3 seed-11 50 mm training run; no v1
or v2 checkpoint may be reused.
