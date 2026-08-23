# ChatGPT handoff summary

## Answers to the 11 audit questions

1. **What Codex completed:** isolated project/inventory, asset and actuator validation, 50/100 replay execution audits, contact/CoM/support-margin code and tests, a frozen replay-derived FSM, 50/75/100 FSM development evaluations, a 96-D actor/146-D critic residual environment, Method B smoke plus all 3 seeds × 3 heights of v34 training and their development gates, and extensive diagnostics.
2. **Code created but not actually run:** Method C remaining stages/gates, formal validation-selection campaign, method freeze, locked test, final B-vs-C/FSM statistics, and locked-test video/report pipeline. Inspection GUI wrappers were created in this audit and only dry-run/help validated.
3. **FSM actual performance:** 50 mm 12/20 (60%); 75 mm 7/20 (35%, 13 timeouts); 100 mm 7/20 (35%, 7 body/link collisions and 6 timeouts). This is development evidence, not locked-test performance.
4. **PPO actual performance:** Method B final checkpoints give 13/20 at 50 mm and 7/20 at 75/100 mm for every seed; 0/9 development gates promote. At 75/100 mm it matches the frozen FSM success counts and failure pattern. Method C has no completed result at the audit cutoff.
5. **Why PPO missed expectations:** weak FSM reference; narrow phase/IMU execution gate and projection; strong penalties on raw actions even when those actions are not executed; zero entropy bonus and tightly bounded exploration; no CoM reward in Method B; missing learning instrumentation. The inspected final policies execute almost no residual, so “training completed” did not become “controller improved.”
6. **Method status:** Method B training/gates complete but failed; Method C has started (seed 11 / 50 mm, status `RUNNING`, intermediate checkpoints exist) but has no completed development gate at the audit cutoff; FSM baseline development evaluation complete at all heights.
7. **Formal FSM/PPO comparison:** no. There is a fair same-manifest development comparison for FSM vs Method B final, but no completed Method C evaluation, validation, method freeze, or locked test.
8. **How to open/use the program:** use the scripts under `scripts\inspection`; they activate the existing IsaacLab path via `conda run` and print exact commands/log paths. Do not use `run_until_success.ps1` for inspection.
9. **Watch FSM in a window:** run `show_fsm_gui.ps1 -HeightMm 75 -ScenarioMode development-success -DryRun`, inspect the command, then rerun without `-DryRun` only when `inspect_project_status.ps1` says GUI is safe.
10. **Watch PPO in a window:** run `show_ppo_gui.ps1 -Method B -Seed 29 -HeightMm 75 -Checkpoint final -ScenarioMode development-success -DryRun`, then rerun without `-DryRun` when safe. `auto` intentionally refuses because no checkpoint is promoted. Method C never falls back to B.
11. **What to send ChatGPT:** start with this report directory’s summary/audit CSVs, plots, source/config evidence list, and small episode evidence. Do not upload all 4.9 GB of telemetry or hundreds of checkpoints. See `CHATGPT_UPLOAD_MANIFEST.md` and `CHATGPT_HANDOFF_BUNDLE_FINAL_20260731_2216.zip`.

## Critical wording

目前 Method C 已启动 seed 11 / 50 mm 训练，但尚未完成且没有 development gate；因此仍不能评价计划中的 CoM-guided Residual PPO。

Do not write “PPO was formally better than FSM,” “CoM-guided PPO was validated,” or “locked testing completed.” A truthful current statement is: “Implemented a frozen replay-derived FSM and a residual-PPO ablation; completed three-seed development training for the no-CoM ablation, which did not pass promotion gates; CoM-guided training and confirmatory testing remain incomplete.”

## Current pipeline state

After two transient empty-exit-code supervisor failures, full-pipeline supervisor attempt 3 launched Method C. The live training process is externally owned; no GUI/evaluation was started and it must not be interrupted. Canonical Method B training results are `COMPLETED`, gates have `passed_execution=true`, and no NaN/OOM/traceback is recorded in their training results.
