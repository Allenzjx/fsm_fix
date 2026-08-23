# V34 formal B/C training registration

## Status

`REGISTERED_BEFORE_FORMAL_V34_TRAINING`.

The selected runtime is
`runtime-v34-selected-phase9-bound-counter-yaw-skid-steer-emergency`.
Real-Isaac realization smoke must pass before launch. The locked-test
manifest remains unread.

## Fixed comparison

- Methods: B (`com_margin_weight=0`) and C (`com_margin_weight=8`).
- Training seeds: 11, 29, 47 for both methods.
- Curriculum heights per seed: 50, 75, 100 mm.
- Each stage: 76,800 local control timesteps, 64 parallel environments,
  4,915,200 transitions.
- Each method: 44,236,800 transitions across nine stage runs.
- B/C total: 88,473,600 transitions.
- Stage 50 starts from scratch.
- Stage 75 resumes the same seed's stage-50 final checkpoint.
- Stage 100 resumes the same seed's stage-75 final checkpoint.
- Randomization: full at 50 mm, light at 75 mm, full at 100 mm.
- Actor, critic, observation, action, PPO hyperparameters, budget,
  randomization, curriculum order, FSM, limits, metrics, and scenario
  identities are identical for B and C.
- The only method difference is the registered CoM reward weight.

## Development gates

Every stage checkpoint is evaluated on the fixed 20-scenario development
height split and receives an immutable `gate_decision.json`. The historical
promotion thresholds remain recorded. Because the original task explicitly
requires complete B/C multi-seed comparisons and describes development
improvement as an ideal rather than a hard reporting condition, a failed
development gate is preserved and disclosed but does not suppress the
remaining pre-registered stage runs when
`-ContinueAfterFailedGate` is used. It does not become a pass and cannot be
used to select or access locked-test results.

Checkpoint selection occurs later on the separate fixed validation manifest
under one frozen lexicographic rule. No locked-test result may influence
training, version choice, or checkpoint selection.

## Operational controls

- Output directories are never reused.
- Existing incomplete or failed runs are retained.
- Each child process and actual Isaac Python PID is tracked.
- NaN, process exit, missing checkpoint, or failed execution stops the
  schedule and preserves diagnostics.
- No global Python/Isaac termination command is permitted.
- Standard training does not record video; selected frozen evaluations do.

