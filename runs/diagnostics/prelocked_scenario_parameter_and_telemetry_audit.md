# Pre-locked scenario-parameter and telemetry audit

## Finding and correction

Before method freeze or locked access, the locked campaign guard was reviewed
for evidence that identical scenario IDs also meant identical scenario
parameters. It already verified manifest/result provenance, exact ID coverage,
controller/height/checkpoint, aggregate counts, and artifact hashes. The audit
is now stricter:

- every episode's obstacle height/front, initial distance/pitch, friction,
  actuator delay, sensor-noise parameters, `environment_seed`, and
  `noise_seed` must equal the corresponding manifest row;
- each telemetry CSV must expose the registered time, environment, pose,
  pitch-rate, margin, and FSM-phase columns;
- telemetry must contain finite time values and cover all environment IDs
  0--99;
- the status artifact must have the registered schema, internally consistent
  active/completed counts totaling 100, and a valid success count.

The result, episode, telemetry, and status hashes remain part of the immutable
locked evidence inventory. The correction changes no evaluator, metric,
scenario, checkpoint, training, or selection definition. The locked manifest
was not opened during implementation or testing.

## Verification

- `src/resume_validation/locked_test_guard.py` SHA256:
  `201b37408bd436f471097f246ce73ec5622ff48ecad96d80738ecd55006556ba`
- Targeted guard/final-audit tests: 4 passed.
- Complete CPU regression: 186 tests, 0 failures.
- Negative tests reject telemetry hash drift and scenario-parameter drift.
