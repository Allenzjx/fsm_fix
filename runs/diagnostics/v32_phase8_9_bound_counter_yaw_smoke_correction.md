# Runtime v32 phase-8--9 bound-speed smoke correction

## Status and chronology

`REGISTERED_AFTER_FAILED_SMOKE_ATTEMPT001_AND_BEFORE_ATTEMPT002`.

The initial registration
`v32_phase8_9_bound_counter_yaw_registration.md` remains immutable evidence
of the pre-code hypothesis. Real-Isaac smoke attempt001 then failed its
mandatory preflight before training or evaluation. This correction was
written after inspecting only that smoke's own preflight output and before
attempt002, checkpoint restoration, or any 20-scenario v32 evaluation.
The locked-test manifest has not been read.

## Failed-smoke evidence

Attempt001 realized:

- phase 8 wheel speed:
  `[-0.075000003,+0.075000003,-0.075000003,+0.075000003] rad/s`;
- phase 9 wheel speed:
  `[-0.100000001,+0.100000001,-0.100000001,+0.100000001] rad/s`;
- phase 10 wheel speed: exact zero;
- phase-8/9/10 wheel-center z: unchanged 3/4/3 mm;
- all-leg IK validity: true in every phase;
- IK-invalid increments: zero in every phase.

The result hash is
`bede9f9a04e5c3834428337d5073be548fa0beb8b26799e9bb34f3438399ba2`.

## Registered correction

The original scalar pre-gain speed floor 0.25 is replaced by phase-aligned
floors `[1/3,1/4]` corresponding exactly to registered speed phases `[8,9]`.
With unchanged phase gains `[3,4]`, both products equal normalized 1.0 and
therefore the unchanged physical wheel-speed bound realizes
`[-0.10,+0.10,-0.10,+0.10] rad/s` in both phases.

The rapid-rise latch preflight oracle is also corrected to include the
phase-8 wheel-speed values it previously omitted.

No other mechanism changes: state-gate thresholds and latch, corrective
phase membership, physical-forward signs, z floors and gains, hard clips,
action bounds, observations, checkpoint, reward, randomization, curriculum,
budgets, development manifest, acceptance gate, and locked-test isolation
remain unchanged.

## Required gates

1. Compilation and all unit tests pass, including phase/floor alignment.
2. New real-Isaac smoke attempt002 proves exact phase-8/9 bound speed,
   phase-10 zero, raw actuator mapping, unchanged 3/4/3 mm z, all-leg IK,
   zero rollback, and the repaired rapid-rise audit.
3. Exact v19 checkpoint restoration proves canonical byte-stable exact-zero
   telemetry.
4. Only then may the fixed 20-scenario development counterfactual run.

V32 from-scratch training remains prohibited unless all gates pass.

## Frozen corrected implementation

- V31 post-run analysis:
  `5707549bd63742aa01f557bf9545dba98c9142341240787a0c709e95b6483025`
- Raw/canonical common config:
  `5c64a81a99bd7a1afce577fcc43d105bf4db7f52364dc2d3c102318fce18b518`,
  `0f341d1fe9aa8439d6be9bb2f3ba2c51999e23772debb9b071ce24ae50114a58`
- `residual_safety.py`:
  `32d50e9b4c5487411f259b485b1afa5e9f58a9d9f76d8308ef7cd0f642cfbe02`
- `residual_rl_env.py`:
  `7e4d227279d2def3c5f266dabcb7c090618cb6f78ec748ab1c7494778b97b0bc`
- `train_residual_ppo.py`:
  `cf0a63845e4d6863fb1cc7f6dc5e26144a6933517471c9ff71b598811a4e8b8c`
- `evaluate_controller.py`:
  `49f652ba17edc4b139fef3fa22dfaae264069ae79ad491836f51d06add4ef2ba`

Compilation and all 166 tests pass. No corrected v32 Isaac result existed
when these hashes were frozen.

