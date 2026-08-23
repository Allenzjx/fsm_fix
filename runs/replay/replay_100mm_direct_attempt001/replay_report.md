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

- Samples: 2500
- Events: 68 / 68
- Forward progress: 0.758307 m
- Episode minimum signed longitudinal support margin: -0.3059825897216797
- Pitch-rate RMS: 0.052445 rad/s
- Invalid margin samples: 522
- Actual non-wheel contacts above 5 N: 0

The post-audit uses actual ContactSensor non-wheel forces. Legacy geometry-only nonwheel counters are retained in telemetry but do not decide collision.
