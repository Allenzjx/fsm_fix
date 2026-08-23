# Method B seed-11 50 mm development-gate attempt003 diagnosis

- Execution status: passed; all 20 registered development scenarios reached a
  recorded terminal outcome.
- Curriculum result: `0/20` strict successes (`0%`), below the frozen
  `16/20` (`80%`) promotion threshold. The method is not promoted to 75 mm.
- Failure distribution: 19 `BODY_OR_LINK_COLLISION`, one `TIMEOUT`.
- Collision bodies: 16 `front_right_bot` contacts (mean terminal force
  13.947 N, maximum 24.381 N) and three `rear_right_bot` contacts (mean
  40.374 N, maximum 49.953 N).
- All episodes had zero residual saturation and zero FSM analytic-IK fallback.
  Therefore clipping and unreachable IK are not the immediate cause.
- The deterministic policy already emitted action L2 approximately `0.61` at
  the initial state and drove 0.864--1.292 m forward before failure. It
  learned a large nonzero residual that disrupted the FSM's support transfer,
  especially at phase 8.
- Reward-scale diagnosis: `top_contact` is currently rewarded every control
  step and `recovery` every phase-9+ step, while collision is penalized only
  once. Over a roughly 9,000-step episode, these occupancy terms accumulate
  thousands of reward units; the one-step `-10` collision term and `+50`
  success term cannot represent the registered safety-first objective. This
  is consistent with the training return near 8,700 despite zero development
  success.
- Corrective method version: integrate occupancy rewards in seconds by
  multiplying `top_contact` and `recovery` by control `step_dt`, increase
  terminal success/collision separation, strengthen common residual/action
  regularization, move every common weight into `ppo_common.yaml`, and record
  the complete PPO config in evaluation provenance. B and C remain identical
  except the CoM weight.
- Result SHA-256:
  `0a4f48dde7f85952c37c5ea51974c420546142ccc51e5db1261f595495aa5402`.
- Episodes SHA-256:
  `bf55d01c94523902eb5755c304026f96839720afcd470edde02eda86d59bb25d`.
- Telemetry SHA-256:
  `b08a6e0f4ead7b775290d2314ee2faaf6562a12ea90e98a2cc4da52e28b1f8d7`.

The failed checkpoint and its 35.8 MB telemetry are retained. The revised
common reward is a numbered development method change and requires training
from scratch; this failed result is not silently replaced.
