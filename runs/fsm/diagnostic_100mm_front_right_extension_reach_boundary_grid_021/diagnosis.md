# Front-right extension reach-boundary grid 021 diagnosis

- Fixed rear-left/rear-right extension: 11.25/15 mm.
- Varied front-right extension: 15/15.5/16/16.5/17 mm.
- Fixed common phase-9 ramp start: 0.4.
- Result: **0 / 25 strict successes**, 12 collisions, 13 timeouts.
- Engineering-admissible result: **0 / 25**.
- Result SHA256:
  `9688c340c214885f314fa1723e42a4ed695c94f329299875ee68349c9a9974cb`.

Every candidate remained at 0/0/0/0 per-leg IK fallback and zero diagnostic
clamp. Thus the actual front-right reach boundary was not encountered by
17 mm.

The best admissible branch continued to improve:

- 15.5 mm peaked at a 1.4864 N simultaneous minimum;
- candidate 19 at 16 mm reached 2.1832 N for one 0.01667 s step;
- candidate 20 at 17 mm reached 2.4076 N and held the full success condition
  for 0.15 s.

At the best 17 mm snapshot, ordered FL/FR/RL/RR upward forces were
4.335/11.528/10.648/2.408 N. This is a tenfold dwell increase over the
one-step crossing in grid 020, but still only one tenth of the unchanged
1.5 s requirement.

Grid 022 covers the remaining legal diagnostic interval at
17/17.75/18.5/19.25/20 mm. The environment rejects offsets above 20 mm, so
this is the amplitude direction's terminal scan. Selection still requires
strict success, 0/0/0/0 fallback, and zero clamp.
