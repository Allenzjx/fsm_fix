# Method-B v15 / v12 checkpoint-64000 development screen attempt001

`EXECUTION_PASS`, `CHECKPOINT_REJECTED`.

- Success: `5/20` (`0001,0002,0010,0012,0016`).
- Failures: nine `BODY_OR_LINK_COLLISION`, four `FSM_PHASE_TIMEOUT`, and two
  global `TIMEOUT`.
- All 50,694 x 122 telemetry rows preserve exact v15 constraints; 5,848
  undefined values occur only in `margin_m`.
- Maximum absolute policy/executed/scaled values:
  `0.3371905` / `0.0986295` / `0.000986295 m`.

Checkpoint 64000 is rejected. Candidate 75200 is next by the pre-registered
order.

Artifact SHA-256:

- result: `bff3ba066f5fcb1b44f44c7078e77fe1d5036af30c8ce286fa312aa8fec3a3f4`
- episodes: `f8054eea5d8c8f895195da4d77cc6e102b534f42109e3fd80ee648586b25c18b`
- status: `ec6a3a7e2c600b5ec77e22a54fa3b19a279286328036691323d3c1ffeecbc53c`
- telemetry:
  `f5263a5dc37567188fa7bb6d2498be94d7d77b59761353de2756dfaa01ea28b0`
- stdout:
  `de0b1d15412fc8f89fc80024edd48c9920371578327dcf1746ee7f1fe87464b6`
- stderr:
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`
