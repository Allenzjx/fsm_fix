# Direct replay audit

Verdict: **FAIL**

## Checks

- PASS: `all_events_dispatched`
- PASS: `command_rows_match_expected_events`
- PASS: `dispatch_jitter_within_one_control_step`
- FAIL: `stable_success_dwell_observed`
- PASS: `no_actual_nonwheel_contact_over_5N`
- PASS: `no_fall`
- PASS: `no_joint_limit_violation`
- PASS: `no_command_limit_violation`
- PASS: `no_numerical_error`
- PASS: `real_contact_sensor_rows_present`

## Metrics

- Samples: 2745
- Events: 159 / 159
- Forward progress: 0.915327 m
- Episode minimum signed longitudinal support margin: -0.2879077196121216
- Pitch-rate RMS: 0.061313 rad/s
- Invalid margin samples: 325
- Actual non-wheel contacts above 5 N: 0

The post-audit uses actual ContactSensor non-wheel forces. Legacy geometry-only nonwheel counters are retained in telemetry but do not decide collision.
