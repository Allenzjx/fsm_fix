# Method-B v21 seed-11 50 mm runtime smoke attempt001

## Disposition

`SMOKE_PASS`. This is an implementation gate, not a performance result.

The real-Isaac training entrypoint completed with one fully randomized
environment and the registered v21 configuration/source provenance.

- Nominal measured pitch was `-0.02244199 rad`; physical residual was exact
  zero.
- A slow `+0.10000000 rad` high-pitch probe executed the climb direction
  `[-0.6, -0.6, +0.6, +0.6]` normalized in phase 8 and the corrective
  direction `[+0.6, +0.6, -0.6, -0.6]` in phases 9 and 10.
- The same probe executed exact zero in phases 7 and 11.
- A `+0.05000000 rad`, `+0.40000001 rad/s` rapid-rise probe executed the
  corrective direction in phase 8 and exact zero in phase 9, proving the
  registered phase-aware conjunction rather than a broad phase gate.
- The fixed 3x gain converted the probe's `0.2` shared drive to `0.6`
  normalized / `6 mm`, within the unchanged `10 mm` hard bound.
- Opposite shared drive remained exact zero. Disabled channels, bilateral
  ties, four-wheel balance, reward/state/contact finite checks, one-shot
  terminal safety, partial reset, and post-terminal reset all passed.

## Provenance

- Result:
  `5c7c4e7a7643f7172132275044286d64f6c9341cb3b6734e518b01f7b55b4171`
- Stdout:
  `4fdf1dab19a73e7208146009d90b7af7f92d1c008ed559a64fd1cad5cadcbee2`
- Stderr:
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`
- V21 raw/canonical config:
  `96d11bc49cc06a0af4248673b59d25117464aa3638c8964b32c844ab25abdb1b`,
  `1db52003b9a2b78ed670702334611a1f3cb132bddbcfb630764977586678b9ba`
- Environment Python PID: `147488`; it exited naturally.

## Next action

Restore the explicit v19 final checkpoint under v21 in a deterministic
one-scenario, five-second development smoke before the fixed 20-scenario
counterfactual.
