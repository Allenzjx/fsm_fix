# Runtime v25 front-right-only IK-feasible emergency registration

## Status

`REGISTERED_BEFORE_ISAAC_EXECUTION`.

Runtime name:
`runtime-v25-front-right-only-ik-feasible-emergency`.

V24 proved that all 863 requested `[0,-1,+1,0]` correction rows were
discarded by the coupled all-leg IK fallback. The rear-left target alone was
invalid on all 863 rows; the valid front-right request was canceled with it.
The frozen pre-code analysis removes only that infeasible rear-left request.

## Registered change

- Corrective wheel-center-z signs change from `[0,-1,+1,0]` to
  `[0,-1,0,0]` on `[FL,FR,RL,RR]`.
- The high-roll and early roll/rate gates, phase-8 latch, historical
  slow-pitch climb branch, actor drive half-space, 0.1 pre-gain corrective
  floor, phase gain 3, 10 mm hard z bound, action mask, and exact-zero
  behavior are unchanged.
- Architecture, observations, rewards, optimizer, randomization,
  curriculum, stage budgets, and method-B/method-C distinction are
  unchanged.
- The locked-test manifest has not been read.

The candidate reconstructed from the frozen v24 targets is workspace- and
joint-limit-valid for all four legs on 863/863 corrective rows. Every v24
collision body was `front_right_bot`.

## Required gates

1. Real-Isaac training-entrypoint smoke must validate the state gates,
   latch, exact action tensor `[0,-0.3,0,0]` at the floor, bounds, finite
   interfaces, phase exit, and reset behavior.
2. Unlike v24, the same smoke must prove physical realization:
   no new residual IK-invalid count, exact requested front-right -3 mm,
   final front-right wheel-center movement toward that request, nonzero
   front-right servo-target change, and exact-zero requests on other legs.
3. The explicit v19 final checkpoint must restore with exact provenance and
   nominal exact-zero execution.
4. The fixed 20-scenario 50 mm development counterfactual must reach at
   least 16/20, retain all 12 frozen-FSM successes plus `0009`, physically
   realize registered corrections, and have zero constraint violations.

V25 training is prohibited until every gate passes.

## Frozen hashes

- Pre-code analysis:
  `6f63e4488a7080fc89da4d70ec8e83c34d912e099fbc4cddaa80e292a4a29061`
- Raw common config:
  `ff56415597dd45fbe9c755c68c44b7332735638dab0bd27d76b7f9bd81ab8f58`
- Canonical common config:
  `261a31c92a3d8e5d39309a86a944e42de4a9a04854c200883dbe1d61cb808653`
- `residual_safety.py`:
  `d91fb91fa05c7618f13fc954d9f5cda059ed749a3688228a9c6aa7c4bf41d3ad`
- `residual_rl_env.py`:
  `453d90b1553679faa7dda5aff4e07cfe9ed81985a24c9e456591968b22252344`
- `train_residual_ppo.py`:
  `d51a1958505a29b55dfe1004060f5c7fd06871c8e309f6e20604d58640d4e2cd`
- `evaluate_controller.py`:
  `32682b53993b849c5b97f5dfdab937a1f3cc470fc564ef4288b581bed22415ef`

Compilation and all 157 tests pass. No v25 Isaac result exists at
registration time.
