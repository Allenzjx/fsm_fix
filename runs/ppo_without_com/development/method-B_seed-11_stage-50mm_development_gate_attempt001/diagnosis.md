# Method B seed-11 50 mm development-gate attempt001 diagnosis

- Status: `FAILED` before any evaluation episode.
- Failure: the evaluator used the removed skrl API
  `agent.set_running_mode("eval")`. Local skrl 2.0 exposes
  `agent.enable_training_mode(False, apply_to_models=True)`.
- Checkpoint loading also warned that the evaluator had not constructed the
  training-time value preprocessor. Although deterministic Actor inference
  does not consume values, a complete auditable checkpoint restore must
  instantiate and restore policy, value, optimizer, observation, state, and
  value modules without skipping registered checkpoint content.
- Fix: use the installed evaluation-mode API and construct the same
  one-dimensional `RunningStandardScaler` value preprocessor as training.
  The evaluator continues to execute `outputs["mean_actions"]`, not sampled
  exploration actions.
- Result SHA-256:
  `7dc4e6d8042f8258f00c90a2d411cf3c42cf1f6f50d099df2bd10f5c7e619bdb`.
- Post-fix suite: 114 passing tests.

This run contains zero evaluation episodes and is not a curriculum result.
A one-scenario integration smoke precedes the full 20-scenario retry.
