# Recovery grid 003 diagnosis

- Execution completed for all 25 candidates on `development-h100-0000`.
- Strict successes: **0 / 25**.
- First terminal snapshots: 22 collisions in phase 10 and 3 collisions in
  phase 9; all 25 contacted `front_right_bot`.
- Result SHA256:
  `f30419b4eff85a7109d0994d54e4b75672bacdd947a4eced22d90303e89641fb`.

The zero-offset control (candidate 12) reproduced the rejected fixed-recovery
case at 145.55 s with 26.8161 N `front_right_bot` contact. The longest-lived
candidate was `dx=-7.5 mm, dz=-5 mm` (candidate 6): it reached 145.85 s and
reduced link contact to 7.9747 N, but front-right wheel support remained 0 N
and its wheel center remained at 0.11295 m while the other wheels were near
the 0.15 m top support plane.

Changing only the unloaded front-right leg therefore does not restore the
support plane. Large negative-z candidates instead caused earlier phase-9
collisions, and positive-z candidates could increase roll/contact force.
The registered next experiment varies a coordinated common wheel-center
height plus a right-side differential, with the rejected load integrator still
disabled and an explicit IK-fallback count.
