# Pre-locked complete technical-evidence freeze

Before validation, method freeze, or locked access, the immutable evidence
boundary was expanded beyond the controller/report Python modules.

The method freeze now includes:

- robot, actuator, environment, FSM, metric, PPO, obstacle, telemetry, and
  all frozen selection/claim/video protocol configs;
- formal B/C training, validation, freeze, locked-test, video, report, final
  audit, and recovery/supervisor PowerShell entry points;
- system inventory, source manifest and hashes, assumptions, and local
  requirements;
- the selected asset manifest;
- URDF validation, USD candidate comparison, and the classified real-Isaac
  integration evidence used by the final technical-claim audit;
- the selected USD asset itself, every formal candidate/result/checkpoint,
  validation evidence, and physical video-smoke evidence.

This ensures the final report cannot mark the SolidWorks/URDF/USD/Isaac,
actuator, CoM/contact, FSM/IK, or comparison chain verified using evidence
that changed after method freeze.

The historical inventory files remain time-stamped discovery snapshots;
current executable configs/sources/scripts are independently hashed as
separate freeze records. The locked manifest remained unread.

- `src/resume_validation/method_freeze.py` SHA256:
  `5db9a69eb5fe78e37a059ed119259751140743ec3de3651cd33d81a6948fa8fb`
- Every newly required evidence path exists.
- Complete CPU regression: 187 tests, 0 failures.
