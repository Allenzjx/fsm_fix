# Front-right extension upper-boundary grid 020 diagnosis

- Fixed rear-left/rear-right extension: 11.25/15 mm.
- Varied front-right extension: 14.00/14.25/14.50/14.75/15.00 mm.
- Fixed common phase-9 ramp start: 0.4.
- Result: **0 / 25 strict successes**, 12 collisions, 13 timeouts.
- Engineering-admissible result: **0 / 25**.
- Result SHA256:
  `3d186996b0033e8e64c77f8aa022c2f0b43f9557f9e090a502f2251ea8baf995`.

All 25 candidates retained 0/0/0/0 per-leg IK fallback and zero diagnostic
clamp. The same 12 candidate IDs as grids 018--019 collided in phase 8 before
the varied offsets activated; the same 13 IDs reached the comparison window.

The measured upward direction produced a real but insufficient admissible
threshold crossing. Candidate 19 at 14.50 mm reached a 2.1649 N simultaneous
minimum at 131.333 s, with ordered FL/FR/RL/RR upward forces of
4.471/11.762/10.377/2.165 N. It met the full force condition for only one
control step (0.01667 s), so the unchanged 1.5 s dwell correctly rejected it.
The other group maxima were 1.0736 N at 14.25 mm and 1.8086 N at 15.00 mm;
the 14.00 and 14.75 mm sampled branches did not produce a positive group
maximum.

Because the complete 14--15 mm sweep was reachable, grid 021 continues only
front-right over 15/15.5/16/16.5/17 mm. It will locate either sustained
support or the actual front-right reach boundary. Selection still requires a
strict environment success, 0/0/0/0 fallback, and zero clamp.
