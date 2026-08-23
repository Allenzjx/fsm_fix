# Method-B v15 / v12 best_agent development screen attempt001

`EXECUTION_PASS`, `CHECKPOINT_REJECTED`.

- Success: `8/20` (`0000,0001,0002,0010,0011,0012,0013,0016`).
- Failures: eleven `BODY_OR_LINK_COLLISION` and one `FSM_PHASE_TIMEOUT`.
  Every collision identifies `front_right_bot`.
- All 48,472 x 122 telemetry rows have uniform width and preserve exact v15
  phase gating, action mask, four-wheel balanced signed projection, and
  physical scaling.
- The 5,849 non-finite values occur only in geometrically undefined
  `margin_m`; the complete action chain is finite.
- Maximum absolute policy/executed/scaled values:
  `0.2080915` / `0.1269641` / `0.001269641 m`.

The final pre-registered checkpoint is rejected. Checkpoint 75200 remains
the best development result at `10/20`, but is ineligible under the
pre-registered `16/20` threshold. The checkpoint screen is therefore
closed without an eligible Method-B policy; the next step must be a new,
numbered, development-only method/training iteration.

Artifact SHA-256:

- result:
  `8182b6fc50f432286dd62c9acdfdbf22583cc9a2839f2c210d888131a99da28c`
- episodes:
  `f9a1b258f7e19fdd334271a74c1d6d43393cd0f1ed3971a02b36104c5097fbd0`
- status:
  `c0fc30c1374abfb4a253ff3f010c2ed2e3db43d112ee39c7c5bdb416f8e40cd7`
- telemetry:
  `1157090fafe38f8ec395877b09c0dff96c98107391dcb116916a4a1cb1dbec61`
- stdout:
  `20b5c7a3edeaf2f70688300ddaedf227ba0f58e659b91afd70a2bd9fd067a7cd`
- stderr:
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`
