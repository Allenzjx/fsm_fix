# FSM 100 mm development attempt 020 diagnosis

- Scenario: `development-h100-0000`.
- Controller/physics change from attempt 019: **none**. This run added only
  explicit world-Z contact-force telemetry.
- Result: **FAIL**, `BODY_OR_LINK_COLLISION`.
- First terminal event: `front_right_bot` at 10.064577 N and 142.0333 s.
- Forward progress: 1.113575 m.
- Terminal front-right wheel-center z: 0.113373 m; the other three wheels
  remained near the 0.15 m top plane.
- Result SHA256:
  `d737ad67f15de29bb3e1e621cb608ac3c26aef2ced76aa6f578196452d8b0a51`.
- Telemetry SHA256:
  `363b606255f3ae29d0c87251b8665c109f071af78c8d85fe86d0b55674880ee6`.

The contact-capture audit compared all 2,841 rows and all 44 columns shared
with attempt 019. There were zero mismatched rows, proving that the added
instrumentation did not alter the physical trajectory.

Across the 301 phase-9/10 samples (127.00--142.00 s), all four wheels were
classified on the top for 15.05 s. However, there was not one sample where
every wheel's world-Z upward force reached the unchanged 2 N threshold.
Consequently the supported-capture wheel stop never activated and the strict
1.5 s dwell was impossible. The best minimum per-wheel upward force was only
1.154396 N at 138.05 s:

- contact-force magnitudes: 6.8623 / 9.6707 / 6.7528 / 10.8595 N;
- world-Z upward forces: 6.8623 / 1.1544 / 6.7487 / 10.8595 N;
- wheel-center z: 0.14983 / 0.12393 / 0.14988 / 0.14976 m.

The limiting front-right contact therefore carried mostly non-vertical force
while its wheel center sank below the top support plane. By 140.00 s its
upward force was zero and its wheel-center z was 0.11447 m, followed by the
latched lower-link collision.

The hash-bearing audit is `contact_capture_audit.json` (SHA256
`ee40ca2ca3004af9354cd55a5d23e7df46816520f122adbaa99139ae772bdc2d`).

The 10% rear recovery cap had been selected from legacy magnitude evidence and
is now explicitly provisional. Diagnostic grid 008 changes only that path cap
over 0/5/10/15/20%, with five repetitions per value to expose environment-index
contact-solver sensitivity. Asset, scenario, controller logic, metrics, safety
thresholds, front support target, and post-transfer wheel speed remain fixed.
