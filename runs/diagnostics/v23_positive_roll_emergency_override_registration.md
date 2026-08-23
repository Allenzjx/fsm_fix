# Runtime v23 positive-roll emergency override registration

Registered before any v23 Isaac execution.

## Frozen mechanism

Runtime identifier: `runtime-v23-positive-roll-emergency-override`.

V23 keeps the frozen FSM and the v19 actor checkpoint interface, but replaces
the ineffective bilaterally tied pitch-correction branch with a deployable
pure-roll correction:

- Phase 8 retains the historical actor-scaled climb direction
  `[-1,-1,+1,+1]` when pitch is at least `+0.09 rad` and no roll emergency
  exists. This is the branch that rescued scenario `0009`.
- Roll at least `+0.10 rad` in phases 8--10 selects corrective wheel-center-z
  signs `[+1,-1,+1,-1]`.
- Phase 8 also selects that correction on the earlier conjunction
  `roll >= +0.06 rad` and `pitch_rate >= +0.35 rad/s`.
- Any phase-8 roll emergency latches correction through phase exit. The latch
  clears on phase exit and every episode reset.
- Corrective positive actor drive has the registered `0.1` pre-gain floor.
  Fixed gain 3 yields `0.3` normalized / `3 mm` physical authority.
- Exact actor zero and the opposite actor half-space remain exact physical
  zero. Wheel-center x and wheel-speed channels remain disabled. The
  unchanged hard wheel-center-z bound is `10 mm`.

The corrective vector has zero four-wheel sum and zero front/rear pitch
moment. With the project convention, positive roll lowers the right side;
left-positive/right-negative z action lowers left body support and raises
right body support, opposing the observed front-right collapse.

No contact truth, scenario identity, obstacle identity, environment index,
or locked-test result enters the controller.

## Development evidence and fixed thresholds

V22 reached 13/20 with exactly the v19 success set despite 1,555 rows at the
3 mm corrective floor. Every collision branch terminated on
`front_right_bot` with positive roll and lost front-right upward support.
The bilaterally tied v19--v22 patterns can generate pitch but no roll moment.

The pre-code analysis is frozen in
`runs/diagnostics/v23_positive_roll_gate_analysis.json` with SHA-256
`7c714bb7dba3aae786a637d57f326d556e31e9345121ff6f7da283fb98a5d208`.

- Frozen-FSM phase-8--10 successes reach at most `+0.0907672 rad` roll.
- V19/v22 successes, including rescued `0009`, reach at most
  `+0.0960836 rad`; none reaches the fixed `+0.10 rad` gate.
- The high-roll gate reaches every frozen-FSM failure and every one of the
  seven current v19/v22 failures.
- Successful trajectories reach at most `+0.330464 rad/s` pitch rate. The
  early phase-8 conjunction reaches only failed `0005, 0006, 0008, 0019`
  and advances first authority by about `0.15--0.25 s`.

These round thresholds and corrective signs were fixed before implementation
validation and before any v23 Isaac run.

## Unchanged invariants

Frozen FSM, metrics, asset, observations/states, network, stochastic bounds,
PPO optimizer, rewards, randomization, curriculum, total training budget,
hard bounds, and Method-B/Method-C distinction remain unchanged.

## Pre-registered decision gates

1. Real-Isaac training-entrypoint smoke must prove exact nominal zero;
   phase-8 slow/high-pitch climb and phase-9 zero; high-roll pure correction
   in phases 8--10; phase-8 early-gate correction and latch persistence;
   exact 3 mm positive-drive floor; latch clear on phase exit/reset;
   phase-7/11 exclusion; zero/opposite-drive shutoff; mask, pure-roll
   pairing, zero-sum/zero-pitch-moment structure, bounds, finite interfaces,
   terminal safety, and reset behavior.
2. Explicit v19 final checkpoint
   `86cf826ee471afc67c65d538013a5f11c4a3600c405bab49193733be95ea242f`
   must pass a one-scenario deterministic restore smoke with exact
   provenance and exact nominal physical zero.
3. The same checkpoint must run all 20 unchanged 50 mm development
   scenarios. Retraining requires at least `16/20`, all 12 frozen-FSM
   successes plus `0009`, nonzero early/latching roll correction, nonzero
   phase-10 roll correction, zero unauthorized actions, and exact structural
   constraints.
4. Any failure prohibits v23 retraining. Passing authorizes exactly one
   from-scratch Method-B seed-11 50 mm run for `76,800` local timesteps /
   `4,915,200` transitions.

## Frozen implementation hashes

- Common config raw:
  `fd8186211625f3efdd1ce17a0b8114d4bca06fdef383ea8302ed8f86707cbb6c`
- Common config canonical:
  `94e11eb98f2d04a931cadaa3bd566cf6a2ef5bb6d1062656362bd82486d75cf7`
- `residual_safety.py`:
  `1c30c91ccc3c8f5be9af3741dc235cb4926bd87bc8072d8d4b59fb572378014a`
- `residual_rl_env.py`:
  `c770cb8cd07ea9d313c7ca6fbbe8e53de06d5718a8a62f05e7dd4df4b56ef46f`
- `train_residual_ppo.py`:
  `e029d83ee1120c364f4feed86a55dd67ab595b1ac473d28fc49e7971176b92d6`
- `evaluate_controller.py`:
  `ed39b203e1c3c5fa5e475f1927abd8094912c139fb57f54cc3726c84fd24de91`
- Frozen FSM:
  `3e4b65ee87a260723d06b7c5ed6e470884917efb2ec6cb4654993e669883e4e9`
- Frozen metrics:
  `6a02b1c09c23245d7ce5b44a6781557f8c578ed56ac11b9d1ef1149c413b30ab`
- Frozen asset:
  `98103315e8ad456881a28a9b3dc77f7aaa8bc9a5200e40c435bea8002c4f81dd`

Python compilation and all `155` unit tests pass. No v23 Isaac result
existed when this registration was written.
