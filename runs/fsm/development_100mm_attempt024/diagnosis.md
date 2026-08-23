# Formal 100 mm attempt 024 diagnosis

- Controller: formal FSM loaded from `configs/fsm.yaml`.
- Scenario: `development-h100-0000`, identical to attempt 023.
- Geometry: FR/RL/RR 18.5/11.25/15 mm, common start 0.4.
- Only control change: stop post-transfer drive on complete geometry OR full
  force support.
- Result: **1 / 1 strict success** at 134.8 s.
- Baseline IK fallback: **0**.
- Result SHA256:
  `bbeb5cb1c4ff04b2fa1c45ef6754069b41c257dbb72717d6a56e378be2246666`.
- Episode SHA256:
  `ef7bb784f59effe3873da1aa34405894df0983a5d17824a777fea9c1c8c0674d`.
- Telemetry SHA256:
  `8083e138b0aca9da4fec7e089a7c476daaec3ee476899f4c02c96605ef513dc3`.

The new trigger captured complete geometry at 130 s and kept front-right y
within -0.4147 to -0.4167 m instead of drifting beyond -0.431 m. The terminal
state had:

- complete-top flags: true/true/true/true;
- upward forces: 5.058/10.542/9.519/3.628 N;
- all-wheels-on-top: true;
- non-wheel collision forces: none;
- joint-limit diagnostic: none;
- baseline IK fallback: zero.

The telemetry tail contains 30 consecutive qualifying records from 133.35 to
134.80 s at 0.05 s record spacing. These correspond to 1.5 s of control
steps; the 1.45 s difference between record timestamps is the inclusive
sampling convention, not a shortened dwell.

This is a valid single-scenario formal success, not yet a development-set
success-rate claim. Attempt 025 will evaluate all 20 development 100 mm
scenarios with the same FSM/config hash.
