# Rear-left independent activation grid 017 diagnosis

- Fixed extensions: front-right 14 mm, rear-left 11.5 mm, rear-right 15 mm.
- Front-left/front-right/rear-right phase-9 start progress: 0.4.
- Varied only rear-left start progress: 0.4/0.5/0.6/0.7/0.8.
- Raw result: **3 / 25 strict successes**, 12 collisions, 10 timeouts.
- Engineering-admissible result: **0 / 25**.
- Result SHA256:
  `48273f6e5303a4b667e06a989074d4cbd29e8a4feb386d070cb800834d4d1550`.

Strict successes occurred at rear-left start 0.5, 0.6, and 0.8. Their best
simultaneous minimum forces were 6.9397, 6.9791, and 6.9543 N respectively;
all three snapshots were close to four-wheel load balance.

Independent delay did not remove unreachable final targets. The three
successes still accumulated 90, 90, and 92 baseline IK fallback steps,
exactly 0/0/N/0 by leg. The near-constant count despite large start-time
changes shows that fallback occurs during the final full-amplitude rear-left
target, not merely during the early ramp. The 11.5 mm rear-left amplitude is
therefore not admissible under any tested phase-9 start.

The largest fully reachable rear-left value remains 11.25 mm. In grid 016 its
best eligible snapshot was limited only by rear-right force:
2.745/14.017/11.684/0.245 N. Grid 018 holds rear-left at 11.25 mm and
front-right at 14 mm, then varies only rear-right extension over
15.0/15.5/16.0/16.5/17.0 mm. A value is selectable only with strict success,
0/0/0/0 fallback, and zero clamp.
