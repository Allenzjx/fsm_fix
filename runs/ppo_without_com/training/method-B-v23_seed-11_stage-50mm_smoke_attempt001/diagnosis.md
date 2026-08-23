# Method-B v23 seed-11 50 mm runtime smoke attempt001

## Disposition

`SMOKE_PASS`. This is an implementation gate only.

The real-Isaac training entrypoint verified the registered v23 roll
emergency semantics:

- Nominal roll `+0.00582019 rad` and pitch `-0.02244199 rad` produced
  exact-zero physical residual.
- A slow `+0.10 rad` pitch probe produced historical climb in phase 8 and
  exact zero in phase 9.
- A `+0.11000001 rad` roll probe produced pure-roll
  `[+0.6,-0.6,+0.6,-0.6]` normalized z action in phases 8, 9, and 10, with
  phase-7/11 exact exclusion.
- A `+0.06999999 rad` roll, `+0.39902040 rad/s` pitch-rate probe triggered
  the early phase-8 pure-roll correction.
- After pitch rate returned to zero and positive shared drive was reduced
  from `0.2` to `0.05`, phase-8 correction remained latched and executed
  exactly `0.1` pre-gain / `0.3` normalized / `3 mm`.
- Entering phase 9 below the high-roll threshold cleared the phase-8 latch
  and executed exact zero.
- Opposite actor drive remained exact zero. Mask, pure-roll pairing,
  zero-sum/zero-pitch-moment structure, hard bounds, finite interfaces,
  one-shot terminal safety, partial reset, and post-terminal reset passed.

## Artifacts

- Result:
  `260b501a6000118d84dd18cd9d760bd2d9e984f5404ac10005bee30d280e2454`
- Stdout/stderr:
  `73cf43867f2cab5fa83ebfbec2878d1e0893c5c02875fbfd4067868112074639`,
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`
- Environment Python PID: `98584`; it exited naturally.

## Next action

Restore the explicit v19 final checkpoint under v23 in a deterministic
one-scenario development smoke. Run the 20-scenario counterfactual only if
restore provenance, finite telemetry, and nominal exact-zero checks pass.
