# Method-B reward-v6 seed-11 50 mm smoke attempt002 diagnosis

## Disposition

`SUPERSEDED_TERMINAL_PATH_NOT_FORCED`. The immutable result is a genuine
`SMOKE_PASS` with no runtime failures. It proves all 22 registered raw reward
tensors were present and finite at `step_dt=1/60`, all five terminal-safety
raw terms were zero during nominal standing, and the exact reward,
environment, model, and trainer source hashes were recorded.

Because the v5 defect concerned the reward on a terminating transition,
attempt002 is not used alone to authorize a long run: it observed the safety
terms only on nonterminal steps. The smoke-only preflight now forces one
environment into the real fall predicate and requires a finite terminal
transition whose weighted `fall` component is exactly -200.

The original result is retained with SHA-256
`d6fa4c98ea8f805afa3974d25cb1a456f95fa9b4bf3a1562b14563ac0931d9fa`;
its TensorBoard event SHA-256 is
`d29181c508994d92528956eaa66cbb5078a58ff36bd9c16b2805367ca9e1cfef`.
Attempt003 repeats the same smoke with the forced terminal-path assertion.
All smoke attempts contribute zero optimization transitions.
