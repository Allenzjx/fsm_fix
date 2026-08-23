# Method-B v16 checkpoint-72000 development screen attempt001

`EXECUTION_PASS`, `CONSTRAINT_PASS`, `PROMOTION_FAIL`.

- Success: `10/20`
  (`0000,0001,0002,0010,0011,0012,0013,0014,0015,0016`).
- Failures: seven `front_right_bot` collisions, two phase timeouts, and one
  global timeout.
- Relative to the FSM, it rescues `0013` but loses `0004/0007/0018`, so the
  net result remains two successes below the baseline and six below the
  promotion gate.
- All `50,786 x 122` rows are uniform. Only 5,851 undefined `margin_m`
  values are non-finite; all five action-constraint violation counts are
  zero.
- Gate off rate is `63.66%` over 14,544 window rows. Maximum
  policy/executed/scaled values are `0.4198749`, `0.1679756`, and
  `0.001679756 m`.

Artifact SHA-256: result
`f1be3cf14e8ec72bac2a089cfcff3e006dba5700561a8e820b06fdcfd399841d`,
episodes
`99efed02b5ff47e5020999f6173f95c3e2ab9525649f0317081c217e3e2f7e58`,
status
`bd5cf5c5452ad8d964d093041f39aca59fa05128b2aeffd3329490a9552b3005`,
telemetry
`e954e2c3dd7e24deb34367804a7064991ec8812330b08cb317b547c930cce712`,
stdout
`0a03ff00e0d27c1cb4e1989474cf379ae9d93fb77a27fd3c0e7eb2da30b155c0`,
stderr
`69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`.

Next: reject checkpoint 72000 and continue with pre-registered
`best_agent.pt`.
