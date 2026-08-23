# Wide front-right/rear-left support grid 013 diagnosis

- Fixed rear-right extension: 15 mm.
- Varied common front-right/rear-left extension: 8/11/14/17/20 mm.
- Five Latin-rotated repetitions per value.
- Raw environment result: **4 / 25 strict successes**, 12 collisions, 9
  timeouts.
- Engineering-admissible result: **0 / 25**, because every raw success
  contained analytic-IK unreachable-target fallback.
- Result SHA256:
  `b994e95b319f1f834a7403c2e4ff9f5003230def8825dc28c04ec8a2d629c11b`.

The four raw successes are the first measured 100 mm episodes to satisfy the
unchanged formal physics condition: all wheels fully on top, every upward
wheel force at least 2 N, bounded roll/pitch and angular velocity, no measured
non-wheel collision above 5 N, and the complete 1.5 s environment dwell. They
are diagnostic evidence that sufficient common extension can create true
four-point support:

- 14 mm, candidate 10: best simultaneous minimum 3.3457 N; snapshot
  4.328/11.240/10.025/3.346 N;
- 14 mm, candidate 19: best simultaneous minimum 3.0560 N; snapshot
  4.323/11.213/10.187/3.056 N;
- 20 mm, candidate 12: best simultaneous minimum 4.1323 N; snapshot
  4.884/10.408/9.439/4.132 N;
- 20 mm, candidate 20: best simultaneous minimum 3.9204 N; snapshot
  5.251/9.963/9.647/3.920 N.

These are not eligible for FSM selection. Their cumulative baseline IK
fallback counts were respectively 243, 238, 216, and 224 steps. The user
protocol explicitly prohibits unreachable FSM wheel-center targets; fallback
must be reported rather than hidden. The environment successes therefore
remain preserved as mechanism evidence only.

The fully reachable 11 mm branches had zero fallback but did not succeed.
Their best simultaneous minimum upward forces were 0 and 0.6493 N, both
limited by rear-right support. The 17 mm branches were also ineligible and
non-monotonic, with 782 fallback steps in the eligible timeout replicates and
a best minimum of only 1.4975 N.

The successful 14/20 mm trajectories terminated in phase 9 while the final
instantaneous IK command was valid. This, combined with the earlier
cumulative fallback, indicates that the source posture is unreachable for the
large offsets early in phase 9 but becomes reachable later. Grid 014 fixes the
lower successful amplitude (14 mm front-right/rear-left and 15 mm rear-right)
and varies only the phase-9 smooth-ramp start progress over
0/0.2/0.4/0.6/0.8. Per-leg fallback counts distinguish whether delaying the
ramp removes every unreachable target while preserving strict success.
