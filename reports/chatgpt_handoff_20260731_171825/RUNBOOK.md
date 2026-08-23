# Inspection and visualization runbook

```powershell
Set-Location C:\robotics_sim\wlr_robot\resume_validation_fsm_residual_ppo
& .\scripts\inspection\inspect_project_status.ps1
& .\scripts\inspection\list_available_controllers.ps1
```

Dry-run the exact command first:

```powershell
& .\scripts\inspection\show_fsm_gui.ps1 -HeightMm 75 -ScenarioMode development-success -DryRun
& .\scripts\inspection\show_ppo_gui.ps1 -Method B -Seed 29 -HeightMm 75 -Checkpoint final -ScenarioMode development-success -DryRun
& .\scripts\inspection\show_fsm_vs_ppo.ps1 -Method B -Seed 29 -HeightMm 75 -Checkpoint final -ScenarioMode development-success -DryRun
```

When the status script reports that GUI launch is safe, omit `-DryRun`. Add `-RecordVideo` to save a development-only replay. `show_ppo_gui.ps1 -Checkpoint auto` refuses while no promoted checkpoint exists; use explicit `best` or `final` and treat the result as diagnostic.

Training dashboard:

```powershell
& .\scripts\inspection\open_training_dashboard.ps1 -DryRun
& .\scripts\inspection\open_training_dashboard.ps1
```

The scripts call the existing `evaluate_controller.py` without `--headless`, force one exact development scenario, use deterministic mean actions, and never start training.
