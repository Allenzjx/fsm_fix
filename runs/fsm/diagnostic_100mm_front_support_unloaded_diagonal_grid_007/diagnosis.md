# Unloaded-diagonal recovery grid 007 diagnosis

- Execution completed for all 25 candidates on `development-h100-0000`.
- Strict successes: **0 / 25**.
- First terminal outcomes: 18 body/link collisions and 7 global timeouts.
- Collision bodies: 12 `rear_left_bot` and 6 `front_right_bot`.
- Terminal phases: 12 in phase 8, 1 in phase 9, and 12 in phase 10.
- All 25 candidates had zero baseline-IK fallback and zero diagnostic command
  clamps.
- Result SHA256:
  `d384e61e1a2334754072f63a1c039dced49d4156cd1bb0ab2941f2c249f67124`.

Twelve phase-8 collisions occurred before the phase-9 diagonal intervention,
despite identical commands, and are contact-solver sensitivity rather than
evidence for or against an extension value. Candidate 0 exactly reproduced
grid 005 candidate 0: it entered phase 10 without collision and timed out with
0.09/14.79/13.86/0.00 N front-left/front-right/rear-left/rear-right wheel
forces.

All seven global-timeout candidates remained collision-free but retained
rear-right force at exactly 0 N; front-left force ranged only 0.35--1.06 N.
Static 0--6 mm front-left/rear-right extension therefore did not restore the
unchanged all-wheel >=2 N dwell and is rejected.

The late collision branch exposed a separate deterministic command defect:
all five inspected phase-10 `front_right_bot` collisions had physical-forward
front wheel commands near -1.32/-1.31 rad/s while both rear commands were
zero. The front-right wheel center then fell from the approximately 0.15 m top
plane to 0.11325--0.11358 m before link contact. Collision-free timeout
branches ended with all wheel commands at zero and could not redistribute
support.

The next formal 100 mm development run keeps the twice-reproduced
collision-free front-right support posture and rejects diagonal extension. It
replaces the partial 100 mm source's post-transfer front-wheel reversal with a
height-conditioned all-wheel physical-forward drive: 0/0.15/0.3 rad/s at
50/75/100 mm during phases 9--10. All metrics and safety thresholds remain
unchanged.
