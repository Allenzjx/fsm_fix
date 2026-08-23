# Method-B v18 / v17-checkpoint 50 mm counterfactual attempt001

`EXECUTION_PASS`, `RETRAINING_AUTHORIZATION_FAIL`.

The unchanged v17 final checkpoint completed all 20 fixed development
scenarios under the registered v18 runtime at 10/20. Failures were seven
`BODY_OR_LINK_COLLISION` episodes and three `FSM_PHASE_TIMEOUT` episodes.
There were no global timeouts, numerical failures, falls, or joint-limit
failures.

V18 gained scenarios 0000, 0001, 0007, 0014, and 0016 relative to the same
checkpoint under v17, but lost 0015, for a net gain of four successes
(6/20 to 10/20). Relative to the frozen FSM it rescued 0013 but lost
0012, 0015, and 0018. It therefore missed both pre-registered retraining
conditions: at least 12/20 and at least six net paired successes over v17.
No v18 retraining is authorized.

The exact 51,793 x 122 telemetry audit found:

- all numeric fields finite except the expected 5,859 undefined
  `margin_m` samples;
- maximum policy / executed action magnitudes
  `0.18085465 / 0.05535655`;
- maximum scaled wheel-center residual `0.5535655 mm` and exact-zero wheel
  speed residual;
- exact phase exclusion, z-only masking, bilateral ties, and four-wheel
  front-negative/rear-positive balance (all error counts/maxima zero);
- gate off in 9,026/15,859 phase-window rows (56.9141%);
- phase-7 off 739/7,360 (10.0408%), phase-8 off 4,593/4,631
  (99.1794%), and phase-9 off 3,694/3,868 (95.5016%).

The observed phase rates closely match the aggregate-action prediction
registered before the run. They also expose the mechanism error: v18 retains
physical residuals during nearly all low-risk phase-7 rows, but suppresses
them during almost all phase-8/9 high-positive-pitch hazard rows. The frozen
FSM development data provide a sensor-observable alternative: successful
phase-8 rows never exceed `0.08677 rad`, while failed rows enter a distinct
positive-pitch branch up to `0.15414 rad`; phase-9 successes stay below
`0.07910 rad`, while its timeout reaches about `0.169 rad`.

The all-episode mean minimum margin is 126.854 mm higher than FSM and mean
pitch-rate RMS is 0.390% lower, but this diagnostic old-checkpoint
counterfactual is not a selectable policy and has lower success. These
values are retained only as descriptive development evidence.

Artifact SHA-256: result
`2e5a8fdd2bd9bf960c83e409e60723a485c81bb3c4e1a2a7c06f23326d5651ee`,
episodes
`10cebca1add332144a4068bcfea82d5de5dc651c807b59806e28ed56b0757840`,
status
`d89d8075aa17a772945e087fead4758dbc7d3f97eb111f16112884fd5e62c67f`,
telemetry
`14b56c264c146ce5af4429367ccb01be5890ccc5f941c1d5cf485c1655bcf81d`,
stdout
`222f63f8ab4b82f389beb0cdc439ed41f54f6decc81714aecd5f1e2e60a5a118`,
stderr
`69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`.

Next: reject v18 training and register a v19 IMU-positive-pitch hazard gate
that preserves the FSM in phase 7 and in nominal phase-8/9 states, while
restoring the zero-preserving residual projection only after the observable
hazard threshold is crossed.
