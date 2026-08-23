# Runtime-v18 two-sigma confidence-gate registration

Registered before any v18 Isaac training or evaluation.

## Evidence available at registration

The v17 Method-B seed-11 final checkpoint reached 6/20 on the unchanged
50 mm development scenarios. Its residual gate was off in only 1,698 of
15,807 phase-7--9 rows (10.7421%), so the low-noise training change
over-corrected v16's predominantly-off deterministic policy to nearly
always-on physical execution.

The v17 recorded shared signed drives are phase-separated. Their medians in
phases 7, 8, and 9 are 0.0266657, 0.0100534, and 0.00785084. Applying the
threshold registered below to those already recorded actions would make the
gate off in 56.12% of all phase-window rows, including 9.9049% in phase 7,
98.4608% in phase 8, and 94.1866% in phase 9. These aggregate action
statistics, not scenario identities or success labels, determine the change.

## Single runtime mechanism change

V18 replaces v17's positive zero gate with a positive confidence deadband:

`executed_shared_drive = max(raw_shared_drive - exp(-4), 0)`.

V17 bounds every action-channel standard deviation at `exp(-4)`. The signed
mean of four independent channels therefore has standard deviation
`exp(-4)/2`; two shared standard deviations are exactly
`exp(-4) = 0.01831563888873418`. This threshold was derived analytically
from the pre-registered v17 maximum exploration standard deviation.

Zero, negative shared drive, and positive drive at or below the threshold
preserve the frozen FSM exactly. Above threshold, only the excess is
projected into the existing balanced front-negative/rear-positive
wheel-center-z direction. The phase window, gains, physical bounds,
architecture, v17 exploration envelope, rewards, optimizer, training
randomization, budget, curriculum, frozen FSM, metrics, asset, and B/C
ablation difference remain unchanged.

## Fixed execution order and decision rules

1. Python compilation and all unit tests must pass.
2. A one-environment real-Isaac training-entrypoint smoke must demonstrate
   finite state/action/reward, exact phase gating, the exact threshold
   subtraction, balanced z projection, and registered v18 provenance.
3. The unchanged v17 final checkpoint must pass a deterministic real-Isaac
   restore smoke under v18.
4. That checkpoint is then evaluated on all 20 fixed 50 mm development
   scenarios under v18. No validation or locked-test scenario may be read.
5. Exactly one from-scratch Method-B seed-11 50 mm v18 run at 76,800 local
   timesteps is authorized only if the counterfactual reaches at least
   12/20, matching the frozen FSM development baseline and improving by at
   least six paired successes over the same checkpoint under v17.
6. Any newly trained checkpoint remains ineligible unless its deterministic
   evaluation reaches the unchanged 16/20 curriculum threshold.

The counterfactual is diagnostic authorization evidence, not a selectable
trained result. No scenario-specific parameter, per-ID exception, checkpoint
screen, or locked-test evidence is permitted.

## Frozen v18 implementation hashes

- `configs/ppo_common.yaml` raw SHA-256:
  `3c6b744266f48155348f9fe8df36ce254221ee9b873abee5b6b3980194e2fcc5`
- canonical common-config SHA-256:
  `ba0b27c4fc565d9ba42167c214fec8002049d90deb03cb5099e16ccc788d475b`
- `residual_safety.py`:
  `8214d6c86a9f3d243f4461fb0f0755139e96ad43a702504961d94d82a08cb273`
- `residual_rl_env.py`:
  `93ac7a9efecaf3c7e7643c6c7036ab3fec2b7be9c18e59b2f7e813ce89438ef8`
- `train_residual_ppo.py`:
  `14c37f0bca4a1d457b8af49945f41f8e683c1a1f4154e7f08d970b87239b283c`
- `evaluate_controller.py`:
  `24d398937fdfdbc3e2c048d0b4e6e98e2a35608ade315d5dbc98b009f025608e`

Python compilation and all 137 tests passed in the registered
`env_isaaclab` environment before this registration.
