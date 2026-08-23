# WLR FSM + Residual PPO Validation

This directory is an isolated, evidence-first validation project for the local
wheel-legged quadruped. It does not edit the source replay or legacy RL
directories. Every formal measurement is produced by Isaac Sim/Isaac Lab and
is tied to a source, asset, config, scenario, or checkpoint SHA256.

## Current status

The inventory, source manifest, conservative USD derivation, actuator mapping,
static/motion integration checks, ContactSensor validation, 1024-sample
runtime analytic-IK check, exact zero-residual check, replay execution, and
frozen-FSM development are complete. Frozen-FSM development results are
12/20, 7/20, and 7/20 at 50/75/100 mm; these are development evidence, not
final claims. Formal runtime-v34 Method-B training is active, followed by the
same three-seed schedule for Method C. Validation, method freeze, locked
testing, video replay, and final resume-number auditing remain hard gates. See
`experiment_state.json` and the live Method-B heartbeat; an absent or failed
result is never replaced with a placeholder metric.

## Runtime

- Windows 11 Home 25H2, build 26200
- NVIDIA RTX 4080 Laptop GPU, driver 581.29
- Conda environment `env_isaaclab`
- Python 3.11.15
- Isaac Sim 5.1.0.0
- Isaac Lab package 0.54.3
- skrl 2.0.0
- PyTorch 2.7.0+cu128
- Physics dt: 1/120 s
- Control dt: 1/60 s

## Environment setup

The audited Windows environment is the existing Conda environment
`C:\Users\kskzz\miniconda3\envs\env_isaaclab`, with Isaac Lab checked out at
`C:\robotics_sim\IsaacLab`. Isaac/Omniverse processes must be launched through
that checkout's `isaaclab.bat`; pure-Python audit/tests can use the environment
Python directly.

```powershell
conda activate env_isaaclab
cd C:\robotics_sim\IsaacLab
.\isaaclab.bat -p -c "import isaaclab, isaacsim, skrl, torch; print('environment imports passed')"

cd C:\robotics_sim\wlr_robot\resume_validation_fsm_residual_ppo
C:\Users\kskzz\miniconda3\envs\env_isaaclab\python.exe -m pytest -q
```

The video path additionally uses the installed OpenCV 4.11, ImageIO 2.37,
and bundled ImageIO-FFmpeg 7.1 binary. No package upgrade is performed during
a frozen experiment; runtime and source hashes are recorded in each result.

Run commands from PowerShell:

```powershell
cd C:\robotics_sim\wlr_robot
powershell -ExecutionPolicy Bypass -File .\resume_validation_fsm_residual_ppo\scripts\run_until_success.ps1
```

The main runner is a recoverable evidence-driven stage machine. It verifies
frozen foundation hashes, finds the first missing formal seed/height stratum,
uses a new attempt directory for recovery, runs validation and method freeze,
and only then authorizes locked testing, video replay, and reports. If a
formal Isaac process is already alive, it records `WAITING` and exits with
code 3 without starting a duplicate. It never retries into an existing
incomplete directory or converts a failed development ideal into a pass.
Before each method's formal curriculum it verifies a method-specific
real-Isaac smoke (and creates a new immutable smoke attempt if none passes);
therefore Method C is not inferred solely from Method B's smoke.

## Canonical asset

The current validation asset is:

`assets\converted\wlr_robot_validation.usd`

SHA256:

`98103315e8ad456881a28a9b3dc77f7aaa8bc9a5200e40c435bea8002c4f81dd`

It is derived from the replay asset
`C:\robotics_sim\wlr_robot\usd\wlr_robot_drive_test.usd`. The only authored
differences are the lower/upper PhysX limits of the eight servo joints. The
exact changes and source hashes are in `assets\manifests`.

## Control semantics

The 12-dimensional residual action is:

1. front-left wheel-center `dx`, `dz`
2. front-right wheel-center `dx`, `dz`
3. rear-left wheel-center `dx`, `dz`
4. rear-right wheel-center `dx`, `dz`
5. four physical-forward wheel-speed residuals

The action chain is:

```text
raw 12-D policy action
  -> actuator delay and actor-observable phase/IMU gate
  -> x residuals remain zero
  -> ordinary high-pitch phase-8 balanced z correction, or
     positive-roll emergency deficient-diagonal z correction
  -> phase gains [3,4,3] for phases [8,9,10], clamped to [-1,1]
  -> emergency phase-9-only counter-yaw wheel-speed correction
     with physical-forward signs [-1,+1,-1,+1] at the 0.10 rad/s bound

record-derived FSM reference
  + bounded wheel-center residual
  -> analytic two-link IK with branch continuity
  -> recorded-safe command envelope and target-rate limiting
  -> articulation position targets

record-derived wheel-speed reference
  + runtime-v34 gated wheel-speed residual (exact zero outside corrective phase 9)
  -> acceleration and speed limiting
  -> articulation velocity targets
```

An exactly zero action bypasses the IK round trip and reproduces the FSM servo
and wheel targets exactly. The fresh Isaac validation measured zero maximum
target error for both command groups.

## Contact and stability definition

The environment records real
`isaaclab.ContactSensor.net_forces_w`. Isaac Lab's net-force sensor identifies
the contacted robot body but not the opposing shape, so the known obstacle box
geometry and wheel position are used to classify lower ground, top, front
riser, and ambiguous edge contact. Riser contact is never accepted as vertical
support.

The longitudinal quasi-static margin is signed:

```text
min(CoM_x - support_min_x, support_max_x - CoM_x)
```

It is valid only with at least two force-supported wheel contacts, sufficient
longitudinal span, and sufficient upward force. Invalid samples and their
reasons are counted; they are not filled with zero or silently discarded.

## Main commands

```powershell
# Recoverable end-to-end entry. Re-running it verifies and reuses immutable
# completed evidence; it never opens locked data before method freeze.
.\resume_validation_fsm_residual_ppo\scripts\run_until_success.ps1

# Inventory, replay parsing, and unit tests
.\resume_validation_fsm_residual_ppo\scripts\00_inventory.ps1

# Fresh asset and actuator integration
.\resume_validation_fsm_residual_ppo\scripts\01_validate_asset.ps1

# ContactSensor, observation, random residual, and zero-residual checks
.\resume_validation_fsm_residual_ppo\scripts\02_validate_sensors_and_residual_env.ps1

# Exact raw-timing replay through the sensor-stable DirectRLEnv
.\resume_validation_fsm_residual_ppo\scripts\03_replay_50mm_100mm.ps1

# Development-only frozen-FSM replay (never use this to overwrite config_freeze)
.\resume_validation_fsm_residual_ppo\scripts\04_build_and_tune_fsm.ps1 -HeightMm 50 -ScenarioLimit 1

# Formal training (3 seeds x 50/75/100 mm x 76,800 local timesteps)
.\resume_validation_fsm_residual_ppo\scripts\05_train_B.ps1 -Attempt 1 -ContinueAfterFailedGate
.\resume_validation_fsm_residual_ppo\scripts\06_train_C.ps1 -Attempt 1 -ContinueAfterFailedGate

# Development-only physical camera/overlay/encoder smoke before method freeze
.\resume_validation_fsm_residual_ppo\scripts\prevalidation_video_smoke.ps1 -Attempt 1

# Validation uses all completed v34 stage-final candidates; it never reads locked test
.\resume_validation_fsm_residual_ppo\scripts\07_run_validation.ps1 -ValidationAttempt 1

# Recompute every validation candidate from raw JSONL and freeze six seed-method selections
.\resume_validation_fsm_residual_ppo\scripts\08_freeze_methods.ps1 -ValidationAttempt 1

# Only after the freeze verifies: 21 evaluations / 2,100 paired locked episodes
.\resume_validation_fsm_residual_ppo\scripts\09_run_locked_test.ps1 -LockedAttempt 1

# Deterministic success/failure/worst-margin/highest-pitch single-scenario replays
.\resume_validation_fsm_residual_ppo\scripts\10_generate_videos.ps1 -LockedAttempt 1 -VideoAttempt 1

# 10,000-draw statistics, CSVs, plots, claims audit, and Chinese resume wording
.\resume_validation_fsm_residual_ppo\scripts\11_generate_report.ps1 -LockedAttempt 1 -VideoAttempt 1

# Independent hash/coverage/table/plot/video/JUnit/final-wording delivery audit
.\resume_validation_fsm_residual_ppo\scripts\12_final_audit.ps1 -LockedAttempt 1 -VideoAttempt 1
```

Both training wrappers use the same implementation, seeds, network,
hyperparameters, 50 -> 75 -> 100 mm checkpoint curriculum, randomization
schedule, and development promotion gates. They differ only in the registered
method label and CoM-margin reward weight (0 for B, 8 for C). Failed
development ideals are preserved and disclosed; `-ContinueAfterFailedGate`
continues the fixed complete-comparison schedule because those ideals are not
licenses to suppress required seeds/heights.

Cross-height warm starts load the prior checkpoint with offset zero. The
`resume_offset_timesteps` trainer option is reserved for recovery inside the
same height. To continue a preserved interrupted schedule without retraining
an earlier completed stage:

```powershell
.\resume_validation_fsm_residual_ppo\scripts\05_train_B.ps1 `
  -Attempt 2 -StartSeed 11 -StartHeight 75 `
  -InitialResumeCheckpoint `
  .\resume_validation_fsm_residual_ppo\runs\ppo_without_com\training\method-B-v34_seed-11_stage-50mm_attempt001\checkpoints\final_agent.pt `
  -ContinueAfterFailedGate
```

The monitor writes a 20-second heartbeat containing the tracked project PIDs,
stage/seed/height, progress, GPU memory, checkpoint, log timestamps, and error
counts. It never enumerates Python processes for blanket termination.

For an unattended multi-day campaign on a host whose AC sleep timeout is
nonzero, `pipeline_keep_awake.ps1` can be launched as a hidden, project-scoped
helper with the exact full-pipeline supervisor PID. It requests only
`ES_CONTINUOUS | ES_SYSTEM_REQUIRED`, does not modify the Windows power plan,
writes an auditable heartbeat under `runs\orchestration`, and releases the
request automatically when that supervisor exits:

```powershell
.\resume_validation_fsm_residual_ppo\scripts\pipeline_keep_awake.ps1 `
  -SupervisorPid <exact-supervisor-pid> -Attempt 1
```

The stage machine writes its current status to
`runs\orchestration\run_until_success_state.json` and an immutable JSONL event
log per invocation. Each event records experiment ID, parent, hypothesis,
changed parameters, unchanged controls, expected/actual effect, result,
evidence, and next action. `-RecheckFoundations` forces fresh inventory,
Isaac asset, sensor/FK, and replay checks; `-StopAfterTraining` stops before
validation without changing any selection.

TensorBoard:

```powershell
conda run -n env_isaaclab tensorboard `
  --logdir .\resume_validation_fsm_residual_ppo\runs `
  --port 6006
```

Standalone frozen-FSM development replay (the output directory must be new):

```powershell
cd C:\robotics_sim\IsaacLab
conda run --no-capture-output -n env_isaaclab .\isaaclab.bat -p `
  C:\robotics_sim\wlr_robot\resume_validation_fsm_residual_ppo\src\resume_validation\evaluate_controller.py `
  --controller fsm `
  --manifest C:\robotics_sim\wlr_robot\resume_validation_fsm_residual_ppo\data\scenario_manifests\development_v2.json `
  --height_mm 50 `
  --output_dir C:\robotics_sim\wlr_robot\resume_validation_fsm_residual_ppo\runs\manual_fsm_check_001 `
  --headless
```

## Frozen success definition

Before formal training/testing, `configs\fsm.yaml` and `configs\metrics.yaml`
must have `frozen: true`, and their exact hashes must match
`configs\config_freeze.json`. Success requires all four wheels beyond the front edge and either on
the top or safely beyond the block, reasonable forward base/CoM position, no
unexpected base/link collision, bounded roll/pitch and angular velocity, a
continuous stable dwell, no joint-limit/numerical error, and completion before
timeout. Root-x alone is insufficient.

## Metric definitions

Primary locked metrics are traversal success, episode minimum valid
longitudinal quasi-static support margin, and support-transfer pitch angular
velocity RMS. Success always uses every episode in its denominator. Continuous
metrics report all valid episodes plus a both-successful paired sensitivity;
missing values and scenario IDs are retained, never replaced with zero.

Secondary episode fields include median minimum margin, negative-margin
duration, maximum absolute pitch, pitch RMS, peak absolute pitch rate,
traversal/termination time, supported-wheel slip distance and ratio,
body/link-collision and joint-limit rates, residual and wheel-speed saturation,
and mean per-step L2 variation of the physically executed normalized residual
command. Slip uses only wheels carrying at least the frozen 2 N upward force
and compares measured wheel surface speed with measured body-frame forward
speed. The project does not label any command-based proxy as energy: no
energy/effort result is published without calibrated power/torque telemetry.

Aggregate continuous estimates and bootstrap intervals give 50/75/100 mm
equal weight. Paired C-vs-FSM, C-vs-B, and B-vs-FSM deltas use identical
scenario IDs, all seeds 11/29/47, and 10,000 stratified bootstrap draws.

## Audit locations

- `system_inventory.json`: hardware/software inventory
- `source_manifest.csv`, `source_hashes.json`: read-only input provenance
- `assets\validation`: fresh integration outputs
- `data\replay_reference`: parsed replay summaries
- `data\scenario_manifests`: development and validation manifests
- `data\locked_test`: pre-registered 300-scenario locked manifest
- `runs`: raw replay, FSM, training, validation, and test artifacts
- `runs\orchestration\run_until_success_state.json`: recoverable stage state
- `runs\ppo_without_com\formal_v34_heartbeat.json`: live registered training heartbeat
- `reports\tables`, `reports\plots`, `reports\videos`: generated only from
  completed locked evidence
- `reports\resume_metrics.json`: machine-readable final result and claim status
- `reports\final_audit.json`, `reports\final_audit.md`: independent final
  delivery audit; honest fallbacks/negative claims produce
  `PASS_WITH_DISCLOSURES`, while missing or drifted evidence produces `FAILED`

The locked manifest was created and hashed before final training, but training
and validation code must not read it. `09_run_locked_test.ps1` first verifies
every immutable file in `configs\method_freeze.json`; only then does the guard
open/hash the registered locked manifest and verify its sidecar.

Final tables and claims can be recomputed from the 21 `episodes.jsonl` files
under the locked run. The report generator checks all hashes, exact paired
scenario coverage, missing continuous metrics, the final pytest JUnit audit,
and video inventory before publishing. Use a new reports directory for an
independent recomputation; never overwrite the original final report.

## Known limitations

- The legacy height-replay collector's manual GPU ContactSensor update failed
  before its first sample and hung during shutdown. That failed attempt is
  retained under `runs\diagnostics`. The isolated DirectRLEnv ContactSensor
  path is stable and is used for formal replay/evaluation.
- The validation USD intentionally blocks command directions not present in
  either accepted replay. Integration reports classify these as expected safe
  limit blocks rather than pretending that every arbitrary direction is safe.
- No resume percentages or improvement claims are valid until all three seeds
  and the paired locked test complete.
