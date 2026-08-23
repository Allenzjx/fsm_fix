# Method-B runtime-v7 seed-11 50 mm smoke attempt001

## Disposition

`PASS`. This run authorizes a new from-scratch 19,200-timestep training run.

All 121 tests and ordinary real-Isaac interface/reward checks passed. A
1.4-rad tilted terminal pose was placed over the obstacle. It produced
`terminated=true`, raw/weighted fall `1/-200`, and finite total reward
`-404.904999` (fall and body-collision safety terms may stack).

After DirectRLEnv auto-reset, the next physics step had sampled target distance
`0.266813397 m`, measured distance `0.265486181 m`, absolute error
`0.001327217 m`, `success=false`, `done=false`, and finite reward. This
directly proves the prior terminal-on-obstacle pose did not contaminate reset.

Common config SHA-256:
`049386620349475e3c2c6800de3a9911ee9a8ec2e817c0bc75fb433e992e5ac1`.
Result SHA-256:
`6dde83c9d1810efae52b6edc62f1818c2edb1aa2aff1d3642de5467d0b55955d`.
Event SHA-256:
`dd932616cf6e5e39946bcc702fdf9acd3df1168a591e3fddd1644eacd347b25d`.

Executed source hashes are recorded directly in `training_result.json`,
including reset geometry source
`bb5cc2c4bca4a89ad79d9f5a2b142ae85685845d8b071b10e2cf87878278ad84`
and environment source
`ed9450b3e865b5cf928432ef43837a6426e1e2fbc596bf69219ec1ed26f91569`.
