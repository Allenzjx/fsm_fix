# V31 bound counter-yaw counterfactual attempt001

## Disposition

`EXECUTION_PASS`, `PERFORMANCE_FAIL`, `13/20 < 16/20`.

The complete fixed development split retains the exact failure set:
collisions 0003/0006/0019 and phase-9 timeouts 0005/0008/0013/0017.
V31 training is prohibited.

Exactly 2,524 rows execute the phase-9-only physical-forward residual
`[-0.100000001,+0.100000001,-0.100000001,+0.100000001] rad/s`.
No other environment or phase has nonzero wheel-speed residual. All
45,944 pre-phase-9 rows and all 13 existing-success state trajectories
are exact v30.

The bound-speed effect is real and directionally correct. Relative to
v30, target terminal yaw moves toward zero by 0.006950--0.011244 rad and
front-right lateral position moves toward support by 2.419--3.397 mm.
The correction nevertheless settles during phase 9 and every target
retains terminal contact `[TOP,TOP,AIR,TOP]`.

The existing phase-8 corrective gate selects 636 rows, all in failed
environments 5/6/8/13/17/19 and none in a current success. This supports
the pre-registered v32 candidate, which retains the same bound output
but authorizes it during dynamic-transfer phases 8 and 9.

## Artifacts

- Result:
  `4c7ea42306ea1a75cba97754be6e93c2d038dd177e34d7f08ee4f4d8352bf9ba`
- Episodes/status/telemetry:
  `265ce71365459366191fdedf244cb9e63f53cfa43c7480cc935e313d122bce8f`,
  `0516536dfe43affb2f77b0030efacf14cf389e5257d5bb803cc555e0ee9eab25`,
  `ddb579bf658359f63d6732213bc8ff18dfc5f788f9fa2ef0e43935ca953dc38d`
- Stdout/stderr:
  `ea7fb42712d526cb8e8f74b5cef79bc5ccb1ca3d9dcaaec574f2db5c924357f8`,
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`
- Environment Python PID `38796` exited naturally.

The locked test remains untouched.
