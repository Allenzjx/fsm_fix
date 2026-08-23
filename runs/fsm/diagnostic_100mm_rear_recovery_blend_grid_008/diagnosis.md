# Rear-recovery blend grid 008 diagnosis

- Scenario: `development-h100-0000`.
- Single varied parameter: maximum rear recovery path fraction
  (`0/5/10/15/20%`), five candidates per value.
- Result: **0 / 25 strict successes**.
- Outcomes: 22 body/link collisions and 3 global timeouts.
- Terminal phases: 12 in phase 8, 1 in phase 9, and 12 in phase 10.
- Collision bodies: 12 `rear_left_bot` contacts in phase 8 and 10
  `front_right_bot` contacts in phases 9/10.
- Every candidate had zero baseline-IK fallback and zero diagnostic command
  clamp.
- Result SHA256:
  `26459a705c50352ec58ff828075e1d74a11024a72e8211475997c0e39ce0fb3c`.

Twelve candidates collided in phase 8, before the varied recovery fraction
could have a physical effect. Their unequal distribution across values is an
environment-index/contact-solver confound and is not evidence that one
recovery fraction is safer. Among candidates that reached the intervention,
every late collision was still on `front_right_bot`.

The formal 10% replicate at candidate 12 exactly reproduced attempt 020's
142.0333 s event, including `front_right_bot` 10.064577 N, front-right
wheel-center z 0.113373 m, and zero front-right upward force.

The three collision-free candidates (0%, 10%, and 20%) all reached the
149.9667 s global timeout without satisfying the unchanged 1.5 s dwell:

- 0%: upward forces 14.0896 / 0.0000 / 0.6407 / 13.5744 N;
- 10%: 13.3707 / 0.0000 / 0.9823 / 14.4694 N;
- 20%: 13.0736 / 0.0000 / 0.7843 / 14.2178 N.

Changing the rear recovery fraction therefore did not restore front-right or
rear-left support and is rejected. The next single-variable grid follows the
measured geometry instead: attempt 020's rear-right wheel center rose to about
0.170 m while the supported top plane was near 0.150 m. Grid 009 retains the
formal 10% rear recovery and varies only phase-9/10 rear-right extension over
0/5/10/15/20 mm. Values are Latin-rotated across environment-index residues,
and completed environments are parked away from contact to avoid repeated
auto-reset slowdown.
