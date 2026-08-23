# Method-B v16 / v12 checkpoint-75200 counterfactual attempt001

`EXECUTION_PASS`, `COUNTERFACTUAL_NEUTRAL`, `V16_RETRAIN_AUTHORIZED`.

- Success: `10/20`
  (`0000,0001,0002,0004,0007,0010,0012,0013,0014,0015`), equal to the
  same checkpoint under v15 but with different paired outcomes.
- Failures: seven `front_right_bot` collisions, one `FSM_PHASE_TIMEOUT`,
  and two global `TIMEOUT`.
- Relative to frozen FSM, v16 retained nine successes, rescued `0013`, lost
  `0011/0016/0018`, and kept the seven-collision aggregate count.
- Relative to v15/checkpoint75200, v16 restored baseline-success branches
  `0000/0007/0015`, while losing other branches; the aggregate remains
  unchanged.
- The gate selected exact zero for 5,739 of 14,346 execution-window rows
  (`40.00%`). In phase 8, successful branches were off about 94--95% of
  rows, whereas collision branches were off only about 79--87%, proving that
  the transformed old policy exposed a state-dependent on/off distinction.
- All 51,148 x 122 telemetry rows have uniform width and preserve exact
  phase gating, mask, sign, four-wheel balance, and physical scaling.
  The 5,848 non-finite values occur only in geometrically undefined
  `margin_m`; the complete action chain is finite.
- Maximum absolute policy/executed/scaled values:
  `0.2794714` / `0.0529198` / `0.000529198 m`.

The old checkpoint was trained under a mean-absolute projection, so its raw
action signs were never optimized as an on/off gate. Aggregate neutrality
therefore does not reject v16. The exact off half-space, 40% observed
selection, restoration of three v15-lost FSM branches, and strong phase-8
outcome separation authorize one new, from-scratch, fixed-budget v16
Method-B training run. Promotion still requires at least `16/20` in an
independent deterministic development gate.

Artifact SHA-256:

- result:
  `8b190c10cee0cfe9ffef9d1274d5fedeb9e33c0170c3333122c5127fd058ee1a`
- episodes:
  `53c8027b1fbf78e3079989aee2753f7681fe244ee27d40c3ba592c769c9a433f`
- status:
  `d3fc2d5d4cbc671802a1b728fbfef7691f8a6aa83aae0bd7e83c261eb095af8c`
- telemetry:
  `11481b6d5a887417f890b1735aa8ec15bede3f09f2c879e79f45800ebb548e67`
- stdout:
  `7cf388d2510ae59fa66dbe49fb5c3fb8c93ee1b54c7f15c75a15ee78158cde7b`
- stderr:
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`
