# Method-B v19 / v17-checkpoint 50 mm counterfactual attempt001

`EXECUTION_PASS`, `RETRAINING_AUTHORIZED`.

The unchanged v17 checkpoint completed all 20 fixed 50 mm development
scenarios under v19 at 13/20. Failures were four
`BODY_OR_LINK_COLLISION` episodes and three `FSM_PHASE_TIMEOUT` episodes.
The success set contains every one of the frozen FSM's 12 successful pairs
plus one rescue, scenario 0009. No FSM success was lost.

The exact 52,615 x 122 telemetry audit found:

- all numeric fields finite except the expected 5,854 undefined
  `margin_m` samples;
- maximum policy / executed action magnitudes
  `0.18171483 / 0.01891932`;
- maximum physical wheel-center residual `0.1891932 mm` and exact-zero
  wheel-speed residual;
- 2,310 nonzero rows out of 2,387 authorized phase-8/9,
  pitch-at-least-0.09-rad rows;
- zero nonzero rows outside that authorized set, including exact zero in all
  phase-7 rows and all below-threshold phase-8/9 rows;
- exact z-only masking, bilateral ties, and four-wheel balance;
- nonzero authority only in environments 0005, 0006, 0008, 0009, 0013,
  0017, and 0019, all members of the frozen FSM failure set.

For the 12 frozen-FSM success pairs, 32,132 rows and all 58 common telemetry
fields have identical physical state, contact, target, reference, and margin
values. Only `action_l2` and reward differ because the policy remains
observable and raw-action regularization is evaluated even while physical
execution is gated off.

All three pre-registered authorization conditions pass:

1. 13/20 is at least 12/20;
2. none of the frozen FSM's 12 successes is lost;
3. 2,310 above-hazard rows execute nonzero residual.

The old-checkpoint counterfactual is diagnostic only. Exactly one
from-scratch Method-B seed-11 50 mm v19 run is now authorized for 76,800
local timesteps / 4,915,200 transitions. Its checkpoint remains
promotion-ineligible until independent deterministic evaluation reaches
16/20.

Artifact SHA-256: result
`cf27190a1f7c2a5341f3fd735cac810286dda5113f30769203d29be483c0e76d`,
episodes
`3df73cac6104a88933623b55ab4c0e12b1770cc6df12aed36b40f9bca1c56548`,
status
`4a18874ab3e5e36d6e3983c1f1ea7b6a8cb0a37ca5d8e3d5ed28648565910dd5`,
telemetry
`5b139e040826f5beea0d8060202d9cc22beb73f5cb42f0d692d0bf5f2b02040c`,
stdout
`457cf1d7a606d9c8eb9ba183cf2069d2f953fb7987db8159c98486ddf64b26fc`,
stderr
`69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`.
