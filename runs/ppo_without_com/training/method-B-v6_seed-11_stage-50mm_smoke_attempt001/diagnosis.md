# Method-B reward-v6 seed-11 50 mm smoke attempt001 diagnosis

## Disposition

`SUPERSEDED_AUDIT_GAP`. The real-Isaac run itself returned `SMOKE_PASS` with
no failures, but it is not the smoke that authorizes full training.

The run proved finite 16x96 actor observations, 16x146 critic states, 16x12
policy actions, exact zero-residual behavior, finite contacts, and a finite
two-environment partial reset under the registered full randomization. It also
recorded the exact v6 config and frozen hashes.

Post-run review found that the preflight recorded reward semantics only from
configuration provenance. It did not enumerate the runtime raw reward tensors
or hash the exact Python source files that executed them. This is an audit
gap, not a physics or numerical failure. The immutable result is retained
(SHA-256
`a5a085715db8973f5ff1e3a4d6ab961a712628d9206f71a1087cf44499135260`);
the 88-byte TensorBoard event SHA-256 is
`57ed0cda15f86066f8e138454d11f573fbe7c2b66740b9f1ecd000c997c3f7a9`.

The trainer preflight now requires the runtime reward-key set to exactly match
the registered set, requires every raw reward tensor to be finite, records all
terminal-safety raw maxima and the control `step_dt`, and hashes the reward,
environment, model, and trainer sources. Attempt002 will repeat the same
real-Isaac smoke with those checks. Both smoke attempts contribute zero
optimization transitions.
