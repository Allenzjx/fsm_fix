# Isaac Sim startup diagnosis

## Conclusion

- GUI exit reproduced by historical attempts: **yes** (four output directories stop before `result.json`).
- Actual historical process exit code: **UNKNOWN**; the old wrapper did not persist it.
- Python traceback in Kit logs: **yes — Kit extension import traceback**.
- Matching Windows `python.exe` / Kit application fault: **no**.
- Renderer/device-lost evidence: **no**.
- Simulation app reached startup complete: **yes**.
- Visible GUI root cause: **VERIFIED: direct-file launch makes the project resume_validation/statistics.py shadow the Python standard-library statistics module; omni.kit.test then fails to import mean during visible extension startup.**
- High-confidence secondary cause: **the original PowerShell launch path did not preserve stdout/stderr separately, child identity, or the true exit code; it therefore made an orderly early shutdown indistinguishable from a crash.**
- Workaround: **HEADLESS/OFFSCREEN capture with owned-process tracking and persisted exit codes**.
- Offscreen recorder stability: **stable across all 14 required primary development captures; all video validations passed**.

The complete Kit log shows the `statistics` module collision during `omni.kit.test` startup, later
app-ready/startup-complete messages, and plugin teardown. It contains no Vulkan/DXGI device-lost or
out-of-memory signature. The safe bootstrap launches the same evaluator as a package module, so the project
module remains `resume_validation.statistics` and cannot shadow the standard library.

## Historical Kit logs

- `kit_20260731_214001.log`: `2026-08-01T01:40:17Z [16,481ms] [Warning] [carb] Recursive unloadAllPlugins() detected!`
- `kit_20260731_214038.log`: `2026-08-01T01:40:52Z [13,155ms] [Warning] [carb] Recursive unloadAllPlugins() detected!`

## Historical GUI output directories

- `fsm_50mm_development-h050-0000_20260731_213855_481`: **STARTUP_EXIT_BEFORE_EVALUATION**
- `fsm_50mm_development-h050-0000_20260731_213957_471`: **STARTUP_EXIT_BEFORE_EVALUATION**
- `fsm_50mm_development-h050-0000_20260731_214035_519`: **STARTUP_EXIT_BEFORE_EVALUATION**
- `fsm_50mm_development-h050-0000_20260731_214057_602`: **STARTUP_EXIT_BEFORE_EVALUATION**

## Classification vocabulary

- **VERIFIED ROOT CAUSE:** direct-file Python launch caused a `statistics.py` standard-library shadow collision in visible Kit extension startup.
- **HIGH-CONFIDENCE SECONDARY CAUSE:** launch/wrapper observability and shutdown lifecycle ambiguity.
- **UNKNOWN:** why Isaac Sim 5.1 graceful `SimulationApp.close()` exceeded the diagnostic shutdown grace after successful 120-frame smokes.
- **WORKAROUND:** deterministic headless camera rendering; visible GUI is not required for completion.

## Current minimal smoke results

- Visible smoke: **COMPLETED_RENDER_SHUTDOWN_TIMEOUT**; 120 render frames completed; recorded exit code `-1`.
- Offscreen smoke: **COMPLETED_RENDER_SHUTDOWN_TIMEOUT**; 120 render frames completed; recorded exit code `-1`; first/last PNG written.
- Headless-no-camera smoke: **COMPLETED_STEPS_SHUTDOWN_TIMEOUT**; 120 simulation steps completed; recorded exit code `-1`.

All three current smokes wrote a passing `result.json` before `SimulationApp.close()` exceeded the shutdown
grace period. Their `-1` exit codes therefore describe forced cleanup after successful stepping/rendering, not a
startup/render failure. The visible controller viewer has not been revalidated; the offscreen renderer is
the supported recording path.
