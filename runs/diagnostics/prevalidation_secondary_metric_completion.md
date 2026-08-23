# Pre-validation secondary-metric completion

- Registered before any validation execution and before method freeze.
- Scope: `evaluate_controller.py` episode and telemetry outputs only.
- Unchanged: FSM, success predicate, primary margin window/definition,
  pitch-rate RMS definition, training environment, reward, PPO, actuator
  limits, scenario manifests, and all active training source files.
- Added measured secondary metrics:
  - traversal time from active control-step count;
  - all-episode body pitch RMS;
  - wheel slip distance and ratio from measured physical joint wheel speed,
    estimated wheel radius, measured body-frame forward speed, and wheels with
    at least the frozen 2 N upward support force;
  - physical wheel-speed saturation rate;
  - L2 variation of the executed normalized residual command.
- Slip distance integrates the mean absolute supported-wheel surface/base speed
  mismatch over control time. Slip ratio divides each supported-wheel mismatch
  by `max(abs(wheel_surface_speed), 0.10 m/s)` before averaging.
- These fields are calculated identically for FSM, B, and C. Validation
  checkpoint selection can therefore use the pre-registered slip criterion
  instead of silently substituting a constant or fabricated value.
