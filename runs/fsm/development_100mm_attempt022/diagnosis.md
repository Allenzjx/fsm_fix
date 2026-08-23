# FSM 100 mm development attempt 022 diagnosis

- Scenario: `development-h100-0000`.
- Controller/physics change from attempt 021: **none**.
- Definition correction: the project subclass no longer lets the inherited
  link-center bounding-box proxy veto the formal full-top prerequisite.
  Actual non-wheel collision rejection remains the unchanged ContactSensor
  external-force magnitude above 5 N.
- Result: **FAIL**, `BODY_OR_LINK_COLLISION`.
- First terminal event: `front_right_bot` at 10.064577 N and 142.0333 s.
- Forward progress: 1.113575 m.
- Result SHA256:
  `0030cf30d6935daac8e8e32d10f75e06820b03b44322f3811368cbb47e52d12e`.
- Telemetry SHA256:
  `b7489e47122d5e228e106ec14a7bc75612e5fadbb0224d45d18aaf8f7a9fd62e`.

The paired telemetry comparison contains 2,841 rows and 58 shared columns.
Exactly one column changed: `all_wheels_on_top`, in exactly 52 rows. All other
57 columns were byte-for-byte value-identical, including base pose, contact
states, contact-force magnitudes, upward forces, wheel positions, support
score, reference commands, and reward. The episode record is also
byte-identical to attempt 021 (SHA256
`8b2ff018b4f4e0514bf042dea6b40cd00e7303883b5b6d826fced96cfdb5a4ec`).
This demonstrates that the correction changed the intended eligibility flag
without changing the physical trajectory.

The corrected aggregate was true for the same 52-sample interval in which all
four formal full-top flags were true: 129.20--131.75 s, or 2.60 s. At 130.00 s
the support score was 0.99988 and the aggregate was true, while the rear-right
upward force was 0 N. Across all 301 phase-9/10 samples:

- all four formal full-top flags: 52 samples;
- every wheel upward force at least 2 N: 0 samples;
- simultaneous full-top and four-wheel upward support: 0 samples;
- strict supported-top dwell: 0.0 s;
- best minimum wheel upward force: 1.154396 N at 138.05 s.

The run therefore correctly remains a failure. The definition correction is
validated and the load-transfer blocker is still physical, not metric
bookkeeping.

The contact audit is `contact_capture_audit.json` (SHA256
`0f249c580082967d58dc19348999ba9f22bb5103b2c8b3e2425090d83bd8eca9`).
Its aggregate row-mismatch count is 52; an independent per-column comparison
confirmed that all 52 mismatches are exclusively the corrected
`all_wheels_on_top` field.

Diagnostic grid 012 repeats grid 011's 25 physical candidates unchanged:
rear-right extension fixed at 15 mm and common front-right/rear-left extension
at 0/2/4/6/8 mm with five Latin-rotated repetitions. With the corrected
eligibility definition, its historical minimum-force and strict-dwell fields
can now measure the intended top-capture state.
