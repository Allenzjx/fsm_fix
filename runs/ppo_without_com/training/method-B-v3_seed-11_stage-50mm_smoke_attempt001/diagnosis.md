# Method B reward-v3 seed-11 50 mm smoke attempt001

- Script status: `SMOKE_PASS`.
- Real IsaacLab checks passed in 16 environments: finite 96-D Actor
  observations, finite 146-D Critic states/values, finite bounded 12-D policy
  samples, finite contacts, exact zero-residual FSM equivalence, and an
  explicit finite two-environment partial reset.
- Effective reward provenance includes the new
  `residual_left_right_asymmetry=-1.0` and
  `residual_magnitude=-0.5` weights.
- Common config SHA-256:
  `337defd27f0020a0d45dd47e13ea774be42ae25d9998c333a2ace675c6c2a50f`.
- Training-result SHA-256:
  `ccd784e237554d720f9049019b3c52fcf9b62e6a9d333fad86b455220db64b79`.

Audit acceptance is deferred. The result hashes the complete common config
but does not directly serialize the effective residual-bound mapping, so the
new 0.20 rad/s wheel-speed residual bound is only indirectly evidenced. Both
trainer and evaluator provenance now record all three effective residual
bounds. A numbered second smoke must verify that direct record before training.
