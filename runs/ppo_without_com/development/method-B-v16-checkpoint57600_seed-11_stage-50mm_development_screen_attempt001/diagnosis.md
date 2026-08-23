# Method-B v16 checkpoint-57600 development screen attempt001

`EXECUTION_PASS`, `CONSTRAINT_PASS`, `PROMOTION_FAIL`.

- Success: `9/20`
  (`0000,0002,0004,0010,0011,0012,0015,0016,0018`).
- Failures: eight `BODY_OR_LINK_COLLISION` episodes
  (`0001,0003,0005,0006,0009,0013,0017,0019`) and three `TIMEOUT`
  episodes (`0007,0008,0014`).
- The candidate loses frozen-FSM success `0007`, rescues no frozen-FSM
  failure, and is therefore a strict subset of the FSM's 12/20 successes.
- All `50,896 x 122` telemetry rows have a uniform schema. Only the expected
  5,855 undefined `margin_m` samples are non-finite; every other numeric
  value is finite.
- Executed action outside phases 7--9 is exactly zero. All disallowed action
  and scaled-residual dimensions are exactly zero. The paired front/rear z
  values and four-wheel balance sum have zero numerical error.
- Maximum absolute policy, executed, and scaled z values are `0.3474104`,
  `0.1175609`, and `0.001175609 m`.
- The physical gate is off in `10,272/13,722 = 74.86%` of phase-7--9
  execution-window rows. Together with the final checkpoint's 71.68% and
  checkpoints 60800/72000 near 64%, the unstable deterministic gate
  occupancy confirms that v16 did not learn a robust mean-action gate.

The complete pre-registered v16 screen is now closed: checkpoint 60800
reached 10/20, checkpoint 72000 reached 10/20, best_agent is
deterministic-policy-equivalent to the already measured 8/20 final agent,
and checkpoint 57600 reached 9/20. None passes the unchanged 16/20 gate.

Artifact SHA-256: result
`61de2bf7f56549a95c945d1c822874954aff29bb05cb8f6b9b8283feae15e28c`,
episodes
`20a113c1dc823edfe7514220dbe7ba5a033f88c57510990ea9bf072492bb21ac`,
status
`d64711b74aa8699cb28872f2741ab37b56693ba92edafd39d5056861503242a9`,
telemetry
`d3005e498e98276a7a664ae32ea32d22812bfe7e76381c8f722724acafd8afd7`,
stdout
`4dbd29972c5cc28615a883c7c3f12a3b202f92fd0fba3772461e16f3659fd08c`,
stderr
`69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`.

Next: reject v16 and make one evidence-driven v17 change that aligns
stochastic rollout exploration with deterministic positive-half-space gate
execution before authorizing another from-scratch run.
