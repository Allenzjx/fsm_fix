# Method-B runtime-v12 seed-11 50 mm smoke attempt001

## Disposition

`FAILED_AUDIT_IMPLEMENTATION`; retained and superseded. The real Isaac
environment executed the registered phase gate, mask, signs, and bilateral
tie correctly, but the smoke script compared the resulting float32 mean to a
separately rounded decimal literal and raised
`Residual physical direction projection failed runtime audit`.

- Environment Python PID: `148044` (exited normally).
- Result SHA-256:
  `f42beded5f7630c59329c8e4de62dcdd59454bb834416f415faee9a3a51421ca`.
- Actual applied action for the nonuniform raw probe was
  `[0,-0.3000000119,0,-0.3000000119,0,+0.7000000477,0,+0.7000000477,0,0,0,0]`.
- Phase-6/7/8/9 scaled maxima were
  `0/0.0070000002/0.0070000002/0`.
- The action-mask and bilateral-tie audits independently returned `true`.

## Root cause and correction

The expected rear value was constructed as a standalone float32 `0.7`, while
the runtime value was the float32 mean of independently represented `0.6`
and `0.8`. Exact equality therefore rejected a correct computation. Attempt
002 constructs the expected vector from the same registered probe operands
using an independent mean expression on the same dtype/device. No environment
or physical projection code changed.
