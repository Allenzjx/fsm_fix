# Method-B v16 checkpoint-60800 development screen attempt001

`EXECUTION_PASS`, `CONSTRAINT_PASS`, `PROMOTION_FAIL`.

- Success: `10/20`
  (`0001,0002,0004,0010,0011,0012,0014,0015,0016,0018`).
- Failures: five `front_right_bot` collisions, three phase timeouts, and two
  global timeouts.
- The successes are a strict subset of the frozen FSM's 12 successes:
  checkpoint 60800 rescues no baseline failure and loses `0000/0007`.
- All `52,692 x 122` rows have uniform width; the 5,859 non-finite values
  occur only in undefined `margin_m`. Phase gate, z-only mask, zero wheel
  speed, balance, and physical scaling have zero violating rows.
- The gate is off in 10,208 of 15,919 execution-window rows (`64.12%`).
  Maximum policy/executed/scaled values are `0.3747768`, `0.1056506`, and
  `0.001056506 m`.

Artifact SHA-256: result
`833338ddf537b6f0e0031cf42d381cdfd72fbecdcc84cdb68fbe93cdc57e4316`,
episodes
`34dd673835be6dd24403232b83ee949f800a4152002bb71e30de5c9f26bfd1a1`,
status
`8620cfce2ccb0c168d00243aa9573834fb03bbde022225ebceda757c7f917a93`,
telemetry
`b2b257c72cf74ad3f4bdd2e2c6845a794e43d10aa7c80bcf7dbea92e0d2f95a8`,
stdout
`db0d5c38b5d42bc6df82769062f1b4089205161c8009e6ece3778691276f7294`,
stderr
`69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`.

Next: reject checkpoint 60800 and continue the frozen order with checkpoint
72000.
