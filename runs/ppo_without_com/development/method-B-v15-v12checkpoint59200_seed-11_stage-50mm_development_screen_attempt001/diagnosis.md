# Method-B v15 / v12 checkpoint-59200 development screen attempt001

`EXECUTION_PASS`, `CHECKPOINT_REJECTED`. The first pre-registered
intermediate candidate completed all 20 fixed 50 mm development scenarios.

- Success: `8/20` (`0000,0002,0010,0011,0012,0013,0015,0016`), below the
  v12-final/v15 result of `9/20`.
- Failures: seven `BODY_OR_LINK_COLLISION`, three `FSM_PHASE_TIMEOUT`, and
  two global `TIMEOUT`.
- All collision terminations identify `front_right_bot`.
- All 51,841 x 122 telemetry rows preserve exact gating, z-only mask, signs,
  bilateral ties, and four-wheel balance. The action chain is finite; 5,839
  undefined values occur only in `margin_m`.
- Maximum absolute policy, executed, and scaled values were `0.3800921`,
  `0.1232363`, and `0.00123236 m`.

The training-window mean-return ranking did not predict the strict fixed
development gate. Candidate 59200 is rejected; candidate 64000 remains next
in the pre-registered order.

Artifact SHA-256:

- `result.json`:
  `1d84398d79f4af2513d01d0a368be771abefafbcbe8c6617d4466e82ff52e365`
- `episodes.jsonl`:
  `f3254f8fd1c6610f6c74ff8728da347d3c31914c1dd609fe09fe59ab7dd7ecde`
- `status.json`:
  `59bc1d842c7d1a3e165eb4535a5ce7713eeb0a42fb824fdeda5f19842ef697cc`
- `telemetry.csv`:
  `ca66709e9e6283975f4978459e1496c020db26eef246f8e4a3fac806154edb6c`
- stdout:
  `5648d22c67e9021780e712254a30b97abb4f717a0f74b62374b0bab8970afc07`
- stderr:
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`
