# Method B reward-v4 seed-11 50 mm smoke attempt001

- Status: `SMOKE_PASS`.
- Real IsaacLab checks passed in 16 environments: finite 96-D Actor
  observations, finite 146-D Critic states/values, finite bounded 12-D policy
  samples, finite contacts, exact zero-residual FSM equivalence, and an
  explicit finite two-environment partial reset.
- Direct effective residual bounds: 0.0075 m x, 0.010 m z and 0.10 rad/s
  wheel speed.
- Direct effective regularization weights:
  `residual_magnitude=-2.0` and
  `residual_left_right_asymmetry=-3.0`.
- Common config SHA-256:
  `b3417383ecb3ab22436764a33c57adb5a374897f87ae680f38bbe64c2275699a`.
- Training-result SHA-256:
  `82ff274ac8c3f74d29792e9c3edb4678f42379b4d57ac839a0838ec359ecccd9`.

The smoke contributes zero optimization transitions. It authorizes one
from-scratch full-budget Method-B v4 training run.
