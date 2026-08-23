# Formal v34 cross-stage resume-offset diagnosis

- Detected: 2026-07-30 during the active Method-B seed-11 50 mm run.
- Scope: PowerShell curriculum orchestration only. The active Isaac training
  process and its imported Python/config provenance are unchanged.
- Defect: `train_curriculum.ps1` accumulated 76,800 timesteps from the prior
  height and supplied that value as `--resume_offset_timesteps` to the next
  height.
- Why this is invalid: the trainer defines that argument as the number of
  already-completed timesteps represented by a recovery checkpoint **inside
  the same stage**. A cross-height warm start is a new 76,800-local-timestep
  stage and must load the checkpoint with offset zero.
- Predicted failure before the fix: at 75 mm the trainer would compare
  `76,800 previous + 76,800 requested = 153,600` against the registered
  75 mm local budget of `76,800` and refuse execution.
- Correction: cross-height curriculum stages now pass `--resume` without
  `--resume_offset_timesteps`. New `StartSeed`, `StartHeight`, and
  `InitialResumeCheckpoint` parameters permit an auditable continuation after
  a preserved orchestration failure without overwriting or retraining a
  completed earlier stage.
- Fairness: the same corrected wrapper is used by Methods B and C. It does not
  alter the environment, policy, reward, randomization, training budget,
  evaluator, FSM, metric definitions, or locked-test data.
- Active-process caveat: Windows PowerShell parsed the already-running
  invocation before this file correction. That invocation may still exercise
  the predicted refusal after its 50 mm training and development evaluation.
  Any resulting failed run directory must be retained. Continuation will use
  a new attempt number and the completed 50 mm checkpoint explicitly.
