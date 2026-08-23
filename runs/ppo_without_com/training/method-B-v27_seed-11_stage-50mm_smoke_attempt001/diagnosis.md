# Method-B v27 seed-11 50 mm downward realization smoke attempt001

## Disposition

`SMOKE_PASS`. This is an implementation gate only.

- Live held phase-8 progress was `0.87999898`.
- Exact high-drive/floor z actions were `[0,-0.6,-0.6,0]` and
  `[0,-0.3,-0.3,0]`.
- Requested and final front-right/rear-left z deltas were both
  `-0.0029999986 m`.
- Per-leg IK validity was `[true,true,true,true]`; residual IK-invalid
  count delta was zero.
- Front-right/rear-left servo-target changes were
  `0.01647520/0.01961753 rad`.
- Inactive coordinates were exact zero. All remaining gate, latch, climb,
  phase, bound, finite, terminal, and reset audits passed.

## Artifacts

- Result:
  `e7b705fa11ed6214fe8427e751d28f37103195af178fb4ad348907eed3cffb55`
- Stdout/stderr:
  `1f1bc1cf8160020d0a6cbc47ef2f9775b5117a90fbd99c17dc471a4546c9c93c`,
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`
- Environment Python PID: `54404`; it exited naturally.

## Next action

Restore the exact v19 final checkpoint under v27 with canonical stride 3.
