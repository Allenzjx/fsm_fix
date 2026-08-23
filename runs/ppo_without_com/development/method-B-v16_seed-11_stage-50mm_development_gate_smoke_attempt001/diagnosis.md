# Method-B v16 seed-11 final-checkpoint development smoke attempt001

`EXECUTION_PASS`, `RESTORE_PASS`, `CONSTRAINT_PASS`.

- The explicit final checkpoint restored with SHA-256
  `c835b6fc5a9e72557de12232aa8f2f86c4850e7ee7c9820ca25c9d2a4123b75e`.
- Frozen FSM, metrics, and asset SHA-256 values match
  `3e4b65ee87a260723d06b7c5ed6e470884917efb2ec6cb4654993e669883e4e9`,
  `6a02b1c09c23245d7ce5b44a6781557f8c578ed56ac11b9d1ef1149c413b30ab`,
  and
  `98103315e8ad456881a28a9b3dc77f7aaa8bc9a5200e40c435bea8002c4f81dd`.
- The run records v16 config SHA-256
  `8dc33c824c1b3576012dc5437db764df04fb8e47ea48c6af9a6a325a0494b193`,
  the zero-preserving balanced z gate, phase window 7--9, and gains
  `[1,1,1]`.
- All `100 x 122` telemetry cells are structurally present and all numeric
  values are finite. Policy maximum absolute action is `0.1524941`.
- The short run observed only phases 0 and 1, so executed action, scaled
  wheel-center residual, and scaled wheel-speed residual are exactly zero.
- The deliberate five-second timeout is diagnostic and is not a performance
  result.

Artifact SHA-256:

- result:
  `e2d5ff2eb0c06ab47f30301c45f8731f9b1b96bdc3d281e9600fea17a330628a`
- episodes:
  `3d8655ec41b06587ea88161e737e531ad77c3d024bf3758c2da5a988d4a64c4b`
- status:
  `f11bd39ef35eb00b69a97cef0711ab299eb52706e4f3b7f1afa166c1d26b8f76`
- telemetry:
  `ffda9ab6ae885a5316c6f62ff0205210b4cf3ec66525b647e2b058b2b689f24d`
- stdout:
  `52a6dea5b7dfa433d39f16aca62c20bdc3fc2503878d15cca58089c9c2847e28`
- stderr:
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`

Next: run the unchanged 20-scenario 50 mm development gate with a 150-second
episode limit. Promotion requires at least 16/20.
