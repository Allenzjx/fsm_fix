# Method-B runtime-v8 seed-11 50 mm development gate attempt001

## Disposition

`FAIL_PROMOTION`. Execution and artifact integrity passed, but the frozen
development result was **10/20 (50%)**, below the registered **16/20 (80%)**
50 mm curriculum gate. This checkpoint is not eligible for validation,
curriculum promotion, warm start, or locked-test evaluation.

- Final checkpoint SHA-256:
  `8a5b9520dad5ecc928623da2d52e5bf08b44611db6fd985bed93f949fb243ae2`.
- Result SHA-256:
  `51cb4cd3d0971af0068ebd5716c624f4082979bb8e9cdaf989e507c94a5a4edc`.
- Episode/status/telemetry SHA-256:
  `0933c4f7318a6268844888f0ec4422ed9e032ae2aa49e684a937b5086ee677fe`,
  `1db952aa26372aa0a6a4a7ca142820a0ae70e0db1699dd322801a8a896798fc7`,
  and
  `827bf97cf44d762369aaff806ec2412973069f5f56ed05e99d1bb3337e363960`.
- Successes were scenarios 0001, 0004, 0007, 0008, 0010, 0011, 0013,
  0014, 0015, and 0018.
- Failures were three `BODY_OR_LINK_COLLISION`, three
  `FSM_PHASE_TIMEOUT`, and four global `TIMEOUT`.

## Paired effect versus the frozen FSM

The frozen FSM succeeded on 12/20 of these exact scenarios. V8 retained eight
of those successes (0001, 0004, 0007, 0010, 0011, 0014, 0015, and 0018),
rescued baseline failures 0008 and 0013, and lost baseline successes 0000,
0002, 0012, and 0016. Unlike v7, which retained none of the baseline
successes, v8 therefore restored substantial baseline anchoring and produced
two genuine paired improvements, but not enough to pass the registered gate.

The actuator-delay subgroups were:

- delay 0: 3 success, 1 collision, 1 global timeout;
- delay 1: 3 success, 2 phase timeouts, 1 global timeout;
- delay 2: 4 success, 2 collisions, 1 phase timeout, 2 global timeouts.

The delay-2 result improved from v7's 0/9 to 4/9. This demonstrates that the
reward-scale correction and phase gate were behaviorally material.

## Terminal and action diagnosis

No episode failed before phase 8. The ten terminal failures separated into:

- three phase-8 `front_right_bot` collisions (0006, 0009, 0017);
- three phase-9 FSM phase timeouts (0005, 0012, 0016);
- four phase-10 global timeouts (0000, 0002, 0003, 0019).

Every phase-10 timeout ended with geometric top flags `1111` and strict
full-wheel-on-top flags `1110`: only the rear-right wheel failed the strict
terminal predicate. Phase-9 policy actions were systematic rather than
numerical noise. For example, across successful phase-9 rows the mean
rear-right wheel-center residual actions were approximately `+0.0859` in x
and `+0.1045` in z, with similarly positive rear-left/rear-right corrections
in timeout rows. Continuing to execute residuals in phase 9 can therefore
oppose the frozen FSM's precise terminal placement, and the four phase-10
timeouts show that suppressing residuals only after entering phase 10 is too
late.

V8 successes took approximately 133--135 seconds. A later direct audit of the
frozen FSM telemetry corrected the original comparison in this paragraph:
the frozen FSM's 12 successful scenarios also terminate at approximately
133--134 seconds, not 44 seconds. Residual execution during phases 2--6
altered an approach segment that produced no v8 failures, but narrowing that
window does **not** increase episode turnover. The 19,200-step budget still
provides only about 2.1 full 150-second episode opportunities per environment.

Phase-8 collision rows also showed weaker, not larger, corrections than
successful phase-8 rows. The collision group mean rear-right x/z actions were
approximately `-0.0042/+0.0341`, versus `+0.0331/+0.0627` in successful
rows. This does not support tightening the already frozen residual bounds; it
supports preserving the FSM approach until the policy reaches the
rear-transfer state on which the useful correction was learned.

## Registered next action

Create common runtime v9 and retrain from scratch with physical residual
execution limited to FSM phases **7--8**:

1. phases 0--6 execute the exact frozen FSM approach;
2. phases 7--8 retain bounded learned correction during the critical
   rear-wheel transfer;
3. phases 9--12 execute the exact frozen FSM terminal placement and settling;
4. policy outputs outside phases 7--8 remain observable and regularized, but
   cannot change physical commands.

Frozen FSM, metrics, asset, success definition, 12-D action semantics,
physical residual bounds, Actor/Critic architecture, PPO hyperparameters,
reward weights, training budget/randomization, seeds, and the B/C-only CoM
reward difference remain unchanged. The runtime smoke must derive its audited
inside/outside phases from the registered window and prove exact zero
execution on both sides before a new full run.
