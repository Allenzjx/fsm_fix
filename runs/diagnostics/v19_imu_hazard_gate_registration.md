# Runtime-v19 positive-pitch IMU hazard-gate registration

Registered before any v19 Isaac training or evaluation.

## Evidence available at registration

The unchanged v17 checkpoint reached 10/20 under v18, below the
pre-registered 12/20 and +6 paired-success retraining gates. Its v18
telemetry showed that the action-confidence gate was aligned with the wrong
states: it remained on in 89.96% of phase-7 rows, but was off in 99.18% and
95.50% of phase-8 and phase-9 rows.

Frozen-FSM development telemetry provides a sensor-observable hazard
separation without using scenario identity:

- successful phase-8 rows never exceed `+0.08677 rad` pitch;
- successful phase-9 rows never exceed `+0.07910 rad` pitch;
- failed branches enter `+0.09` to about `+0.169 rad`;
- phase-7 pitch distributions overlap between outcomes and therefore do not
  justify physical residual authority.

Pitch is already part of the actor's IMU/proprioceptive observation. No
simulator-only contact state, friction, randomization parameter, environment
seed, or scenario ID enters the new gate.

## Single runtime mechanism change

V19 replaces the v18 action-confidence deadband with a signed IMU hazard
gate. Physical residuals can execute only when both conditions hold:

1. FSM phase is 8 or 9; and
2. real-IMU pitch is at least `+0.09 rad`.

Below that threshold, at negative pitch, in phase 7, and in phases 0--7 or
10--12, the physical result is exactly the frozen FSM. When the hazard gate
opens, the four raw z channels use v16/v17's zero-preserving shared-drive
projection: non-positive shared drive stays off; positive drive executes the
existing balanced front-negative/rear-positive z correction. Wheel-center x
and wheel-speed residuals remain exactly zero.

The `+0.09 rad` threshold is fixed above the maximum successful phase-8
pitch envelope with a 0.00323-rad gap and before any v19 result. Architecture,
v17 exploration envelope, action bounds, rewards, optimizer, training
randomization, budget, curriculum, frozen FSM, metrics, asset, and B/C
ablation difference remain unchanged.

## Fixed execution order and decision rules

1. Python compilation and all unit tests must pass.
2. A one-environment real-Isaac training smoke must prove exact below-gate
   FSM preservation, above-gate balanced z authority, phase exclusion,
   finite interfaces/rewards, terminal safety, reset, and v19 provenance.
3. The unchanged v17 final checkpoint must pass a deterministic restore smoke
   under v19.
4. That checkpoint is evaluated on all 20 fixed 50 mm development scenarios.
   No validation or locked-test scenario may be read.
5. Exactly one from-scratch Method-B seed-11 50 mm v19 run at 76,800 local
   timesteps is authorized only if the counterfactual:
   - reaches at least 12/20;
   - loses none of the frozen FSM's 12 successful scenario pairs; and
   - records at least one nonzero above-hazard residual row, proving the
     result is not merely an inert FSM duplicate.
6. A newly trained checkpoint still requires the unchanged 16/20 curriculum
   threshold for promotion.

The old-checkpoint counterfactual is diagnostic authorization evidence, not
a selectable trained result. No per-scenario exception or result-dependent
gate is permitted.

## Frozen v19 implementation hashes

- `configs/ppo_common.yaml` raw SHA-256:
  `f115a3a4e435c70721ffdc44468e0352e71ca66f8187610f6ecd3cda112a8f93`
- canonical common-config SHA-256:
  `3ffba6ff7e809a4244ebcee93e38b359a080ab7f594c87c73bd6e22f39ea31bf`
- `residual_safety.py`:
  `8209dec556979c0e6db32b3c5825262672ad57aac4896e95bf65882c7302ddc5`
- `residual_rl_env.py`:
  `fcadaca601955127673c3b44bd5d4f841f1003e37a77f4c5fafc95031ceef572`
- `train_residual_ppo.py`:
  `bd3282ec2431a4d775bc400fa56ddb9e73575c33d695229e62f461fea79de73d`
- `evaluate_controller.py`:
  `c87a4ed88420bf1d12a474f51bb6509cc30db0f2e23ff1503b587c578974ca64`

Python compilation and all 144 tests passed in `env_isaaclab` before this
registration. Two intermediate documentation-assertion failures were fixed
before hashes were frozen and before any v19 Isaac launch.
