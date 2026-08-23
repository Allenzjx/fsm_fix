# FSM 100 mm development attempt 021 diagnosis

- Scenario: `development-h100-0000`.
- Controller/physics change from attempt 020: **none**. This run added only
  explicit per-wheel full-top, aggregate top-eligibility, support-score, and
  wheel-y telemetry.
- Result: **FAIL**, `BODY_OR_LINK_COLLISION`.
- First terminal event: `front_right_bot` at 10.064577 N and 142.0333 s.
- Forward progress: 1.113575 m.
- Result SHA256:
  `907dcdf85682270865cee031be80d9dd21dee72e17647499f104a8d521baeb34`.
- Telemetry SHA256:
  `923b6666082961aaba21977f84f9d5ac9c971b5c4671bdab3210c2ed4d875074`.

All 2,841 rows and all 48 telemetry columns shared with attempt 020 were
identical. The added instrumentation therefore did not alter the measured
physical trajectory.

The new geometry fields isolated a definition mismatch. During phases 9--10,
all four wheels satisfied the formal full-wheel-on-top geometry for 52
consecutive 50 ms samples, from 129.20 through 131.75 s (2.60 s). Roll and
pitch were bounded and the support score was approximately 0.9999 throughout
that window, yet the inherited aggregate `all_wheels_on_top` flag was false in
all 301 post-transfer samples.

Source inspection showed that the inherited aggregate additionally required
`_nonwheel_obstacle_contact_count == 0`. That count is not measured contact
force: it is a link-center bounding-box estimate. It can therefore veto a
geometrically valid full-top state even when the formal protocol's actual
ContactSensor external-force threshold has not been crossed. This conflicts
with `metrics.yaml`, which rejects a body/link collision only when measured
non-wheel external force exceeds 5 N.

The force-bearing success condition still never occurred in attempt 021:
zero post-transfer samples had all four upward wheel forces at or above 2 N.
Thus removing the proxy veto alone is not expected to turn this trajectory
into a success; it is required so future load-transfer experiments are judged
against the declared metric rather than an undocumented surrogate.

The hash-bearing contact audit is `contact_capture_audit.json` (SHA256
`a5d85ae8895da579ae46a50cee32c8adc45e69293e6a8a5ed0c468cd800799a7`).

The project subclass now recomputes the full-top prerequisite from per-wheel
full-top geometry, bounded tilt, and support score. Formal non-wheel collision
rejection remains the unchanged ContactSensor magnitude threshold in
`_get_dones()`. Attempt 022 repeats the same scenario and controller to verify
that this definition correction changes only eligibility telemetry unless the
complete force-bearing dwell is actually reached.
