# Method-B v13 / v12-checkpoint development counterfactual attempt001

The full 20-scenario development-only counterfactual completed normally under
environment Python PID `123164`. It passed execution and achieved `8/20`
successes (`40%`), versus `7/20` for the same v12 final checkpoint under v12
semantics. This diagnostic checkpoint/config pairing is not promotion
eligible.

- Successes: `0000`, `0001`, `0002`, `0010`, `0011`, `0012`, `0013`,
  `0016`.
- Relative to v12: retained five, gained `0002/0012/0013`, and lost
  `0015/0019`.
- Failures: six `front_right_bot` collisions, five `FSM_PHASE_TIMEOUT`, and
  one global `TIMEOUT`.
- Delay groups (success/total): delay 0 = `2/5`, delay 1 = `2/6`, delay 2 =
  `4/9`.

All 52,476 x 122 telemetry rows have exact phase gating, z-only masking,
signs, bilateral ties, and four-wheel balance. The action chain is finite;
5,845 undefined values occur only in `margin_m`. Maximum absolute policy,
projected, and scaled wheel-center values were `0.3428333`, `0.0984901`,
and `0.000984901 m`. Successful phase-8 rows averaged the exact balanced
physical vector
`[-0.00038943,-0.00038943,+0.00038943,+0.00038943] m`.

V13 reduced phase-8 collision failures from seven to six and reduced the
global timeout count from three to one, but phase timeouts increased from
three to five. The paired net gain was only +1. Evidence therefore does not
yet justify a full v13 retrain. The next diagnostic should retain the same
safe projection but extend its physical window through phase 9, where the
remaining bottleneck now occurs.

Artifact SHA-256:

- `result.json`:
  `1a9f6ff60a624c361a5b4bcd15ba60c1e87c75f3f435f2063f428d7502df0100`
- `episodes.jsonl`:
  `e1cc50947f04a49b1a8305d718994420b9e9b61a2c64ce9929d0298b1a2008c8`
- `status.json`:
  `35732fe1a602f03686cdfb8297da6015c0e46e1437f551c6908aa413c6d9b6d9`
- `telemetry.csv`:
  `1a5c46ccfc746d089a6183789823f489909531537a7cb06c3b53a51585a6968d`
- stdout:
  `b2b2f65e20c0c6a39d6e4468a4173ad97cf4164bca0fcb065aca297cb9beee61`
- stderr:
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`
