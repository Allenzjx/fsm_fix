# FSM implementation audit

The authoritative runtime FSM is the vectorized implementation in `src\resume_validation\residual_rl_env.py`, not merely the standalone `FSMController` helper.

- Phase enum and names: `src\resume_validation\fsm_controller.py:10-23`.
- Height-conditioned phase boundaries: `src\resume_validation\fsm_phase_schedule.py:13-48` and runtime use at `src\resume_validation\residual_rl_env.py:1015-1047`.
- Contact-gated monotonic transitions and three-step latch: `src\resume_validation\residual_rl_env.py:971-1047`.
- Phase-specific fallback wheel commands: `src\resume_validation\residual_rl_env.py:1054-1122`.
- Baseline support geometry/load balancing: `src\resume_validation\residual_rl_env.py:1145-1224` and `1289-1353`.
- IK nearest-branch selection and safe limits: `src\resume_validation\residual_rl_env.py:1251-1287`.
- Dynamic phase timeout: `src\resume_validation\residual_rl_env.py:1880-1911`.
- Formal success dwell and safety termination: `src\resume_validation\residual_rl_env.py:1841-1943`.

The phase order is front pair first and rear pair second. Phase gates use “at least one” and then “both” contacts within each pair; this is not a strictly one-wheel-at-a-time FSM. The 50 mm replay provides the complete rear reference; the partial 100 mm replay is combined with height-conditioned rear preparation and recovery. Servo references use zero-order hold rather than geometric interpolation (`src\resume_validation\fsm_trajectory.py:26-47`).

There is contact debounce (3 control steps) and contact-milestone latching, but no backward transition hysteresis. Fallbacks are stop-at-gate, conservative approach/rear/post-transfer wheel commands, all-leg IK fallback to the baseline, and terminal safety predicates. Servo targets are rate limited after IK; wheel targets are acceleration limited only for nonzero PPO residual. Exact zero action bypasses both residual rate-limit paths and equals the FSM reference.

Frozen config: `configs\fsm.yaml`; SHA-256 `3e4b65ee87a260723d06b7c5ed6e470884917efb2ec6cb4654993e669883e4e9`. Selected validation asset SHA-256 `98103315e8ad456881a28a9b3dc77f7aaa8bc9a5200e40c435bea8002c4f81dd`. All formal Method B training/evaluation provenance records the same current FSM hash, and the config file predates the v34 formal runs; there is no evidence it changed after those runs.

75 mm uses normalized-time command interpolation between 50/100 mm replays and linearly interpolated phase/support geometry, but not every tuning parameter is a simple midpoint: support unloading, rear-transfer speeds, and post-transfer speed have explicit 75 mm anchors.

Development results are in `fsm_results.csv`. The 100 mm baseline already fails 13/20 episodes (7 body/link collisions, 6 global timeouts). Many 75/100 mm timeouts finish in late `DRIVE_CLEAR`; representative plots are under `plots\episodes`.
