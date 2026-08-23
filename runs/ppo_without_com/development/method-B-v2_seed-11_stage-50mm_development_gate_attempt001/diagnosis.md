# Method B reward-v2 seed-11 50 mm development gate attempt001

- Status: execution `PASS`; curriculum promotion `FAIL`.
- Deterministic final checkpoint:
  `c02026df0f913c6761e1354f6026928421896d5e570dd1e1c848ce13852d8706`.
- Registered scope: all 20 fixed 50 mm development scenarios, 150-second
  per-episode limit, deterministic mean action.
- Outcome: `0/20` success versus the registered `16/20` promotion minimum.
- Failures: 20 `BODY_OR_LINK_COLLISION`; 18 terminated on
  `front_right_bot` (mean/max force 14.20/22.95 N), and two on
  `rear_right_bot` (mean/max force 36.02/42.54 N).
- Episode end time: mean 113.795 s, minimum 110.50 s, maximum 130.85 s.
- Forward progress: mean 0.9183 m, range 0.8686--1.1859 m. The policy moved
  through phase 8 rather than exploiting a stationary reward.
- Terminal full-wheel-on-top patterns: 18 episodes had only front-left and
  rear-right fully on top; two had only front-left fully on top.
- Residual saturation rate was zero and the frozen FSM baseline IK had zero
  invalid samples.
- Phase-8 deterministic residuals were systematically asymmetric:
  - front-left/front-right center dx means: -3.67/-3.97 mm;
  - rear-left/rear-right center dx means: +4.64/-0.06 mm;
  - front-left/front-right wheel-speed residual means:
    -0.040/+0.030 rad/s;
  - rear-left/rear-right wheel-speed residual means:
    +0.090/+0.105 rad/s.
- Mean phase-8 normalized action L2 was 0.667. The policy-to-actuator table
  contains 45,538 finite rows and 122 columns.
- Aggregate mean episode-minimum quasi-static margin was 0.12718 m and mean
  support-transfer pitch-rate RMS was 0.06255 rad/s. These are failure-episode
  diagnostics, not evidence of improvement.
- Artifact SHA-256 values:
  - `episodes.jsonl`:
    `d057c99056f82dcdffe92f2b3d1431b3690478dc7e896ccaca9779a9787fe47f`
  - `result.json`:
    `b252eba5c469bc9e4949b9bd040c6482cd9831c8d27a8ca2c2688090f9708784`
  - `status.json`:
    `9ad803571e65c891290632ce8a3676ab9fe64ebfa7590f12b209c6b3db3f5193`
  - `telemetry.csv`:
    `1345f59acfbfd2204e0c5dd7eb5e2097b4c048ba8da26dba1f896c47c93d31bc`

Reward v2 fixed the earlier early-collision/reward-scale defect, but the final
policy converted the frozen FSM's mixed baseline result into systematic late
right-link collisions. Reward v3 will retain the frozen FSM, metrics, success
definition, observations, network, PPO budget, seeds, and B/C ablation. It
will (1) strengthen normalized residual-magnitude anchoring, (2) add one
common left/right residual-asymmetry penalty, and (3) reduce only the
wheel-speed residual bound. Training must restart from random initialization;
no v2 checkpoint will be reused.
