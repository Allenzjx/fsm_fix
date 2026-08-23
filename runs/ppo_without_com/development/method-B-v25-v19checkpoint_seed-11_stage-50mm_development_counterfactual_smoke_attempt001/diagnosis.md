# Method-B v25/v19-checkpoint restore smoke attempt001

## Disposition

`CONTENT_PASS`, `PROTOCOL_MISMATCH`; repeat required before promotion.

The explicit v19 final checkpoint and v25 config/source provenance are
exact. Telemetry is `299 x 122` because this invocation used
`record_stride=1` instead of the established restore-smoke stride 3.

- Only semantically undefined `margin_m` is non-finite (`2` rows).
- Executed action, scaled wheel-center residual, and wheel-speed residual
  are exact zero.
- Checkpoint SHA-256:
  `86cf826ee471afc67c65d538013a5f11c4a3600c405bab49193733be95ea242f`.
- Common-config SHA-256:
  `ff56415597dd45fbe9c755c68c44b7332735638dab0bd27d76b7f9bd81ab8f58`.
- Evaluation-source SHA-256:
  `32682b53993b849c5b97f5dfdab937a1f3cc470fc564ef4288b581bed22415ef`.

Joining by exact `(env_id,time_s)` yields the same 100 canonical
0.05-second samples as the v24 restore. Every one of their 122 columns is
bit-exact, including NaN placement. This supports content equivalence but
does not erase the invocation mismatch.

The 5 s diagnostic timeout is not a traversal result.

## Artifacts

- Result:
  `5859d770094cb5023bba28eadcf9a23f5e832d230fbfcfa656a0067f25abf432`
- Episodes:
  `3d8655ec41b06587ea88161e737e531ad77c3d024bf3758c2da5a988d4a64c4b`
- Status:
  `fdfafd24d19f30c979000374453876e15fcfafd2a6edce03cad408ef74ef2d54`
- Telemetry:
  `82220feda282cbe304dafe8bf74b4ca33fc2432afd500ff56ad176544ffaca58`
- Stdout/stderr:
  `3e812643ba55d10d0d3c2e21cca111a8d6e4ff4b742c78031aaa44432b8fae29`,
  `69b88143604bcb1c3325db0bf8c4c3359be2d7084fd61fd13186a9ab533c76d2`
- Environment Python PID: `172052`; it exited naturally.

## Next action

Repeat in a new directory with unchanged inputs and `record_stride=3`.
