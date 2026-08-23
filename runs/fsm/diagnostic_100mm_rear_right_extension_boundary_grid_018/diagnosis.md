# Rear-right extension boundary grid 018 diagnosis

- Fixed front-right extension: 14 mm.
- Fixed rear-left extension: 11.25 mm, its zero-fallback upper bound.
- Varied rear-right extension: 15.0/15.5/16.0/16.5/17.0 mm.
- Fixed common phase-9 ramp start: 0.4.
- Result: **0 / 25 strict successes**, 15 collisions, 10 timeouts.
- Engineering-admissible result: **0 / 25**.
- Result SHA256:
  `1ae8ff68de5e4cb8626dd4ef3a15d8ce96b99c035db63413074834965fe5393a`.

Rear-right values above 15 mm were not admissible in any long-lived branch:

- 15.5 mm accumulated rear-right fallback and peaked at 1.3934 N minimum;
- 16.0 mm reached 2.1735 N for one 0.01667 s step but accumulated 674
  rear-right fallback steps in that timeout;
- 16.5 mm accumulated 251--386 rear-right fallback steps;
- 17.0 mm reached 2.5045 N for 0.15 s but accumulated 639 rear-right fallback
  steps.

Per-leg counts were exactly 0/0/0/N, proving that only the varied rear-right
target became unreachable. The 15 mm control remained the upper observed
zero-fallback value. Increasing rear-right cannot create an admissible 1.5 s
dwell.

At the reachable 14/11.25/15 mm front-right/rear-left/rear-right state, the
best force snapshot from grid 016 was
2.745/14.017/11.684/0.245 N: front-right was heavily loaded while rear-right
was nearly unloaded. Grid 019 therefore holds rear-left/rear-right at their
reachable bounds and varies only front-right extension downward over
10/11/12/13/14 mm to redistribute load without increasing any unreachable
target. Selection requires strict success, 0/0/0/0 fallback, and zero clamp.
