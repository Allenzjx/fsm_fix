# Method-B runtime-v7 seed-11 50 mm development gate attempt001

## Disposition

`FAIL_PROMOTION`. Execution and artifact integrity passed, but the frozen
development result was **2/20 (10%)**, below the registered **16/20 (80%)**
50 mm curriculum gate. This checkpoint is not eligible for validation,
curriculum promotion, warm start, or locked-test evaluation.

- Final checkpoint SHA-256:
  `0f00a8207fff1fb096f9124f4e9b0df47cae9d9d579914913f47ef5f90ab704d`.
- Result SHA-256:
  `437be4b4c28909504682fca9ba5c94d256a00879c2867c22328d3b5f3910f053`.
- Episode/status/telemetry SHA-256:
  `915b3c593c267dea553215613cee051a0daa0e566d4e848b65b04e1f6c7a4488`,
  `3aef273888a25644416a7b0da4b2b7e11ecfa5ce50e3054d8314d84601b8cc09`,
  and
  `0ed8445d7def807bc3420d2bf0a0d3c2e39f0da6bec2501b9767d22066524f74`.
- The two successes were scenarios `development-h050-0008` and
  `development-h050-0013`.
- Failures were eight `BODY_OR_LINK_COLLISION`, one `FSM_PHASE_TIMEOUT`,
  and nine global `TIMEOUT`.
- All nine actuator-delay-2 scenarios failed.

## Paired failure diagnosis

The frozen FSM succeeded on 12/20 of these exact scenarios. V7 retained none
of those 12 successes. Its two successes instead rescued scenarios 0008 and
0013, which were a baseline collision and phase timeout respectively. This is
not a disturbance-generalization failure alone; it is loss of the zero
residual controller's already demonstrated safe behavior.

Terminal telemetry separates two failure modes:

- six phase-8 `front_right_bot` collisions;
- two phase-10 `rear_right_bot` collisions;
- nine global timeouts, all in phase 10;
- one phase-9 FSM phase timeout.

Every phase-10 global timeout ended with geometric top flags `1111` but
full-wheel-on-top flags `1110`; the residual policy prevented the rear-right
wheel from reaching or retaining the strict full-top terminal state. The two
phase-10 collisions likewise moved failure from the frozen baseline's
successful terminal sequence to `rear_right_bot` contact.

The policy correction was materially larger than reward v4 despite unchanged
physical residual bounds. Across all telemetry rows, deterministic action L2
rose from **0.11758** in v4 to **0.24512** in v7. Phase-10 mean action L2 rose
from **0.1690** to **0.2597**. Reward v6 correctly converted continuous
residual magnitude and asymmetry terms to per-second integrals, but retained
the prior per-control-step weights `-2/-3`. At 60 Hz this weakened their
effective baseline-preservation pressure by approximately 60 times. The
observed larger residuals and complete loss of baseline successes are
consistent with that scale change.

## Registered next action

Create a common runtime/reward v8 for both B and C:

1. fix the local skrl rolling-episode accumulator indexing bug without
   modifying the installed package;
2. make residual execution zero in the approach/terminal-settle phases and
   active only during the contact maneuver, so phase 10 converges to the
   frozen FSM endpoint;
3. re-scale the time-integrated residual magnitude/asymmetry weights to retain
   the v4 per-second baseline-preservation strength.

Frozen FSM, metrics, asset, success definition, 12-D action semantics,
physical residual bounds, Actor/Critic architecture, PPO hyperparameters,
training randomization, seeds, and the B/C-only CoM reward difference remain
unchanged. Unit tests and a real-Isaac safety/terminal-gate smoke must pass
before a new from-scratch training run.
