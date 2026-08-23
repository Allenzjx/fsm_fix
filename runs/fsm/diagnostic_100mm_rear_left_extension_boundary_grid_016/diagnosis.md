# Rear-left extension boundary grid 016 diagnosis

- Fixed front-right extension: 14 mm.
- Fixed rear-right extension: 15 mm.
- Fixed common phase-9 ramp start progress: 0.4.
- Varied rear-left extension: 11.00/11.25/11.50/11.75/12.00 mm.
- Raw result: **2 / 25 strict successes**, 12 collisions, 11 timeouts.
- Engineering-admissible result: **0 / 25**.
- Result SHA256:
  `1d59d4aeabbacb09f36b73e2730c979311d8e3c9f72ae4e15c109a6f17f71972`.

The strict successes occurred at:

- 11.50 mm, candidate 19: best minimum 6.9161 N; snapshot
  7.277/6.916/7.627/6.926 N;
- 12.00 mm, candidate 20: best minimum 6.2038 N; snapshot
  6.536/7.889/7.681/6.204 N.

Both successes had 90 fallback steps, exactly 0/0/90/0 by leg, and zero
command clamp. They are rejected for formal selection despite their large
force margins.

The boundary is discontinuous in engineering admissibility:

- 11.25 mm branches remained fully reachable but peaked at only 0.2447 N
  simultaneous minimum;
- 11.50 mm created strong, sustained support but the successful path crossed
  90 unreachable rear-left targets;
- 11.75 and 12.00 mm long-lived branches also accumulated rear-left fallback.

No fixed common ramp can simultaneously make the early rear-left path
reachable and provide the later load-bearing amplitude. Grid 017 therefore
preserves the successful 11.5 mm rear-left amplitude but gives that leg an
independent phase-9 ramp start. Front-right and rear-right remain at start
0.4. Rear-left alone varies over 0.4/0.5/0.6/0.7/0.8. Selection requires
strict success, 0/0/0/0 fallback, and zero clamp.
