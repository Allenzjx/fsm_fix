# Method-B runtime-v9 seed-11 50 mm development gate attempt001

## Disposition

`FAIL_PROMOTION`. Execution and artifact integrity passed, but the frozen
development result was **6/20 (30%)**, below the registered **16/20 (80%)**
50 mm curriculum gate. This checkpoint is not eligible for validation,
curriculum promotion, warm start, or locked-test evaluation.

- Final checkpoint SHA-256:
  `fafc0ada9dadb12f49ebe98d7fbc258ff432d0a20d2ade3d2af6cccfb8834140`.
- Result SHA-256:
  `8749e9c320d7722d8abaa25daab32b8905e4f828547fa6a5d90653639fa4bdd3`.
- Episode/status/telemetry SHA-256:
  `4c2b8748c23ea4e44094582a195205d72592a47b14559ef1c7cd143842ca556d`,
  `c8f0460ac413fd6d1f3db260d815c25f9666e60a0e40429a370fa427b015435f`,
  and
  `59167f179a9dff4e950ba6d376a56c80ba4722f62e43d3cb8b1d8e327c98f020`.
- Successes were 0008, 0010, 0012, 0013, 0016, and 0018.
- Failures were eight `BODY_OR_LINK_COLLISION`, two
  `FSM_PHASE_TIMEOUT`, and four global `TIMEOUT`.
- Delay subgroups were 1/5, 3/6, and 2/9 for delays 0, 1, and 2.

## Paired effect

V9 retained only four of the frozen FSM's 12 successes (0010, 0012, 0016,
0018), rescued baseline failures 0008/0013, and lost eight baseline
successes. Relative to v8, it retained four of ten successes, gained
0012/0016, and lost 0001/0004/0007/0011/0014/0015. Restricting phase execution
therefore did not preserve the baseline as hypothesized.

Seven collisions terminated in phase 8 at 107.60--111.70 seconds and one
additional front-right collision terminated in phase 10 at 130.50 seconds.
All eight reported `front_right_bot` force above the 5 N collision threshold.
The two phase timeouts ended in phase 9; the four global timeouts ended in
phase 10 with strict full-top flags `1110`.

## Directional action diagnosis

V9 learned the opposite vertical correction from the safer v8 behavior:

- v9 phase-7 front-left/front-right z actions were approximately
  `+0.03/+0.03`, while rear z actions were negative or near zero;
- v9 phase-8 collision rows retained positive front z actions
  (`+0.031/+0.025`) and weak rear z lift (`+0.009/+0.007`);
- v8 successful phase-8 rows instead used negative front z
  (`-0.038/-0.050`) and positive rear z (`+0.036/+0.063`).

V9 collision rows also had larger phase-8 action L2 than success rows
(`0.0894` versus `0.0755`). The observed contact is therefore consistent with
the learned positive front-wheel-center z residual lifting the already
transferred front assembly into a front-right lower-link collision. The
bounded symmetric action box is insufficient as the only safety constraint
for this contact phase.

## Correction to the v8 duration diagnosis

The v8 diagnosis stated that the frozen FSM succeeded in approximately 44
seconds. Direct re-reading of
`runs/fsm/development_50mm_current_config_attempt043/telemetry.csv` shows its
12 successes actually terminate at **133.20--134.45 seconds**, essentially
the same duration as v8 successes. That earlier 44-second comparison was
wrong and is superseded by this artifact-backed correction.

Consequently, narrowing the execution window did not increase episode
turnover. A 19,200-step run represents 320 simulated seconds per environment,
only about 2.1 full 150-second episode opportunities. V9's repaired tracker
reported just 36 completion windows. Sparse collision/success terminal
feedback was therefore underexposed.

## Registered next action

Create common runtime v10 with:

1. the existing physical phase window 7--8;
2. a phase-independent physical direction projection for wheel-center z:
   front-left/front-right z residuals may only be non-positive, and
   rear-left/rear-right z residuals may only be non-negative;
3. raw policy actions still observable and regularized, with projected
   physical actions separately exposed in telemetry;
4. a full-development budget of 76,800 local timesteps (1,200 x 64),
   providing about 8.5 episode horizons per environment.

Frozen FSM, metrics, asset, success definition, 12-D policy action order,
absolute residual bounds, network, PPO hyperparameters, randomization,
seeds, and B/C-only CoM difference remain unchanged. V10 must pass unit and
real-Isaac projection/gate smoke audits before a new from-scratch run.
