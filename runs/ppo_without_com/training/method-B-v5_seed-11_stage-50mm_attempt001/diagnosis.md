# Method-B reward-v5 seed-11 50 mm training attempt001 diagnosis

## Disposition

`ABORTED_INVALID_OBJECTIVE`. This run is retained as negative evidence and
contributes zero accepted training budget. No checkpoint from this directory
is eligible for development, validation, curriculum promotion, warm start, or
locked-test evaluation.

The original `training_result.json` remains byte-for-byte as written by the
trainer (`status: RUNNING`). The process was deliberately terminated before
normal completion after the objective defect below was demonstrated; this
sidecar records the truthful terminal disposition without rewriting the
partial run as a completed experiment.

## Observed evidence

- The exact from-scratch process ran with 64 environments, full registered
  50 mm randomization, seed 11, and the requested 19,200 local-timestep
  budget.
- The process reached progress counter 9,517/19,200. Its latest durable
  checkpoint is `checkpoints/agent_8000.pt`, SHA-256
  `224e82dbf201143bab1554337375e93d0ea873daf7707c65941206e5216d01bf`.
- The checkpoint contains 77 tensors and 785,093 tensor elements; every
  element is finite. Finite parameters do not make the checkpoint valid when
  the optimized objective is wrong.
- At the audited 9,024-step report, completed episode length had minimum 168,
  mean 8,472, and maximum 8,991 steps, while completed episode return had
  maximum -17.6176, mean -1,486.234, and minimum -1,593.584.
- A 168-step unsafe termination therefore received a much better return than
  long-lived trajectories. Code inspection confirmed that fall, numerical
  failure, and phase timeout terminated an episode but had no corresponding
  terminal reward term. Joint-limit termination carried only -2.
- Several state/rate costs (`pitch_rate_sq`, `excessive_tilt`, `slip`,
  `residual_magnitude`, residual asymmetry, `joint_acceleration`, and wheel
  saturation) were charged once per 60 Hz control step rather than integrated
  over elapsed time. In particular the slip term alone could accumulate about
  -1,300 over a 6,500-step episode, rewarding early termination as escape from
  future cost.

## Safe termination and retained artifacts

Only the verified environment Python PID 15576 for this run was terminated.
No broad Python or process-name kill was used. The process and its related
launch processes exited, and all partial logs/checkpoints were preserved.

Artifact hashes at diagnosis:

- partial `training_result.json`:
  `f33d8a1ec3b67c627094812f31e16d98af9116ca602c8764ab244691f0c3c931`
- `checkpoints/agent_8000.pt`:
  `224e82dbf201143bab1554337375e93d0ea873daf7707c65941206e5216d01bf`
- TensorBoard event:
  `a258e5cb973bdb4fae8a786bdf34cf2e755d4c5155664d5b52c1e7a3eff0177e`

## Registered next action

Create common reward v6. Continuous state/rate costs will be multiplied by the
control `step_dt`; fall, numerical failure, phase timeout, joint-limit
termination, and body collision will each carry an explicit one-shot -200
safety term. FSM, frozen metrics, observations, action dimensions/bounds,
network, PPO hyperparameters, training randomization, seeds, and the B/C-only
CoM ablation remain unchanged. Run unit tests and a real-Isaac smoke before a
new from-scratch full-budget attempt.
