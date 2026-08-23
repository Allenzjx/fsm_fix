# Files to provide to ChatGPT

## First upload (small, sufficient for planning)

- `HANDOFF_SUMMARY.md`
- `METHOD_STATUS_AND_PPO_FAILURE.md`
- `IMPLEMENTATION_AUDIT.csv`
- `EXPERIMENT_MATRIX.csv`
- `CHECKPOINT_INVENTORY.csv`
- `PPO_FAILURE_HYPOTHESES.csv`
- `FSM_IMPLEMENTATION.md`, `fsm_phase_table.csv`, `fsm_results.csv`, `fsm_failure_reasons.csv`
- `observation_schema.csv`, `action_schema.csv`, `residual_control_chain.md`
- `PPO_TRAINING_ANALYSIS.md`, `training_curve_summary.json`, and the seven top-level plots
- `episode_diagnostics.csv` plus representative timeline PNGs
- `ACTIVE_PROCESS_STATUS.md`, `active_processes.json`, `GIT_STATUS.md`, and `RUNBOOK.md`

The generated `CHATGPT_HANDOFF_BUNDLE_FINAL_20260731_2216.zip` contains these inspection outputs plus the key source/config files below. It intentionally excludes checkpoints, full telemetry, and every locked-test scenario file. The earlier bundles are superseded by this timestamped final bundle.

## Key source/config evidence

- `configs/fsm.yaml`, `metrics.yaml`, `ppo_common.yaml`, `ppo_without_com.yaml`, `ppo_with_com.yaml`, `environment.yaml`, `obstacle_train.yaml`, `robot.yaml`, `config_freeze.json`, `experiment_protocol.yaml`
- `src/resume_validation/residual_rl_env.py`, `residual_safety.py`, `ppo_models.py`, `train_residual_ppo.py`, `evaluate_controller.py`, `fsm_controller.py`, `fsm_phase_schedule.py`, `fsm_trajectory.py`, `reference_tensor.py`, `reward.py`, `curriculum_gate.py`, `checkpoint_selection.py`
- `scripts/train_curriculum.ps1`, `run_until_success.ps1`, `formal_training_recovery_supervisor.ps1`, `full_pipeline_supervisor.ps1`

## Optional targeted evidence

- The selected seed-29 75/100 mm `result.json` and `episodes.jsonl` files for FSM and Method B final.
- One `best_agent.pt` and one `final_agent.pt` only if ChatGPT will inspect tensors directly. Their hashes and module keys are already in `CHECKPOINT_INVENTORY.csv`.
- Full telemetry only for a single named scenario if a new analysis specifically needs raw steps; do not upload the entire 4.9 GB corpus.

## Explicit exclusions

- Do not upload or inspect `data/locked_test/manifest_v2.json`; it has not been authorized or executed.
- Do not upload all 856 checkpoint files.
- Do not present diagnostic development plots as confirmatory evidence.
