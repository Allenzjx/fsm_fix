# Front-support recovery grid 005 diagnosis

- Execution completed for all 25 candidates on `development-h100-0000`.
- Strict successes: **0 / 25**.
- First terminal outcomes: 23 body/link collisions and 2 global timeouts.
- Terminal phases: 10 in phase 6, 3 in phase 7, 3 in phase 9, and 9 in
  phase 10.
- Collision bodies: 12 `front_right_bot`, 11 `base_link`.
- All 25 candidates had zero baseline-IK fallback and zero diagnostic command
  clamps.
- Result SHA256:
  `496f3607683b65ac094d989e597c40439c9113ba00a6ba8ddabb1e41000fe1d4`.

The zero-offset control (candidate 7) reproduced the prior late
`front_right_bot` failure at 145.05 s. Large positive front-right hip offsets
caused early phase-6 `base_link` collisions and are rejected.

Candidate 0 (`front_right_hip=-3 deg`, `front_right_knee=-15 deg` relative to
the registered support target) was the only collision-free candidate to enter
phase 10. It ran to the 150 s global timeout with no safety termination,
IK fallback, or command clamp; terminal pitch/roll were -0.00211/-0.01536 rad
and support margin was 0.22386 m. It did not satisfy the unchanged success
condition; its legacy front-left/front-right/rear-left/rear-right
contact-force magnitudes were 0.09/14.79/13.86/0.00 N. These are not world-Z
upward components. The low-magnitude front-left/rear-right
diagonal therefore prevented the required all-wheel force dwell.

Candidate 12 also avoided collision to the global timeout but remained in
phase 9 with the original opposite diagonal split: 11.85/0.00/2.44/14.44 N.
The evidence selects candidate 0 as the next controlled base posture, not as a
success.

Grid 006 keeps candidate 0's phase-6 front-right posture fixed and varies only
smooth phase-9/10 wheel-center extension on the measured unloaded front-left
and rear-right diagonal from 0 to 6 mm independently. It retains an exact
zero-offset reproduction and the same first-terminal and IK-fallback audits.
