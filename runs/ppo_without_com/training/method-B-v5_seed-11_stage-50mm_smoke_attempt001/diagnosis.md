# Method B reward-v5 seed-11 50 mm smoke attempt001

- Status: `SMOKE_PASS`.
- Scale: 16 real Isaac environments, 8 control timesteps and 128
  transitions; no optimization and no reusable checkpoint.
- Full training randomization was active and directly recorded:
  - initial distance half-range 0.025 m;
  - initial pitch half-range 0.020 rad;
  - friction 0.90--1.20;
  - actuator delay 0--2 control steps;
  - sensor noise standard deviation 0--0.005.
- Actor observation, critic state, and policy action shapes were
  16×96, 16×146, and 16×12.
- Actor/critic/action/contact outputs were finite.
- Exact zero residual equivalence passed.
- Forced partial reset of environment IDs 0 and 15 passed with finite root
  poses.
- Reward provenance states that top-contact, recovery, and stuck occupancy
  are integrated by `step_dt`.
- Common config SHA-256:
  `356b3144ac2175b21380d8accb33b8e0ad6190e93fbb78e256a7a69323e3451a`.
- Training-randomization config SHA-256:
  `86f1476a82197624d1be1901bb27c0c40f0df32c36d710b1b044b2299d846267`.
- Training-result SHA-256:
  `e3a89c4dcb03ad827bb1efab27f12ecbf21e1c30b527a4476af3dfc399ef129a`.

This smoke authorizes a from-scratch Method-B seed-11 50 mm v5 run with the
exact registered full randomization and 19,200-timestep budget.
