# Method B reward-v3 evaluator smoke attempt001

- Status: `FAILED` before environment construction and before any episode.
- Failure: `UnboundLocalError` while serializing effective residual bounds.
- Cause: the new evaluator provenance field read `cfg.residual_bounds` before
  `make_residual_env_cfg(...)` assigned `cfg`.
- No policy action, transition, telemetry row, or performance observation was
  produced.
- `result.json` SHA-256:
  `87fc06de4adbe2a005b7081e1bfed2a5f26f560927b00fc80b2c3f955dc58083`.

The field is now populated immediately after environment-config construction.
Pycompile and all 117 tests pass. The failed directory remains immutable and
a numbered attempt002 must repeat the evaluator smoke.
