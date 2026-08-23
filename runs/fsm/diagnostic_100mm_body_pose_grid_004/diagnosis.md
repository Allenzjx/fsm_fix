# Body-pose recovery grid 004 diagnosis

- Execution completed for all 25 candidates on `development-h100-0000`.
- Strict successes: **0 / 25**.
- First terminal snapshots: 23 phase-10 and 2 phase-9 collisions; all 25
  contacted `front_right_bot`.
- Result SHA256:
  `987c90976dc4bb39da8d3694212bb6f25f1b2e598444685af0cd9b89149363ba`.

Seventeen candidates were fully applied with zero baseline-IK fallback and
still produced no success. The longest fully applied candidate used
`common_z=+5 mm`, `right_delta_z=-5 mm` (left legs +5 mm, right legs zero):
it reached 145.80 s, but front-right wheel support remained 0 N and its wheel
center was 0.11266 m. Candidate 6 lasted 145.833 s but had two IK fallbacks and
is not eligible as applied evidence. The zero-offset control again reproduced
145.55 s and 26.8161 N.

Both single-leg and coordinated phase-9 geometry changes leave the front-right
wheel trapped below the top support plane after the rear transfer. The next
registered diagnostic therefore moves earlier: it smoothly varies the
front-right hip/knee support posture through phase 6 and holds it through
phase 10, entirely inside the recorded-safe command envelope. This tests
whether link clearance must be established before rear transfer.
