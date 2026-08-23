# Method B seed-11 50 mm training attempt 001 diagnosis

- Status: `FAILED` on the first Trainer action request, before any environment
  transition or optimizer update.
- The 64-environment preflight itself was finite and zero residual exactly
  reproduced the FSM.
- Failure: the Actor implementation read `inputs["states"]`, which is the
  146-dimensional privileged Critic state in local skrl 2.0.0, while its
  first layer correctly expects the 96-dimensional Actor observation. This
  caused `64x146` by `96x256` matrix multiplication to fail.
- Fix: `ResidualPolicy` now consumes only `inputs["observations"]`;
  `ResidualValue` continues to consume privileged `inputs["states"]`.
  A regression verifies that changing a 146-dimensional privileged state
  cannot change the Actor result for fixed observations.
- The training preflight now calls `agent.act(observation, states)` and records
  the finite action shape/magnitude, so this interface is checked before both
  smoke and full optimization.
- Training-result SHA-256:
  `adb45003c87e67f4ed7cb1126520ed02c80535f7a1e604cbb849616f39eff4d8`.

No checkpoint exists and this run contributes zero training transitions.
Retry uses attempt 002 with all formal hyperparameters unchanged.
