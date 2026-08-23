# Host idle-sleep guard

- Date: 2026-07-30
- Scope: operational continuity only; no experiment, simulator, controller,
  scenario, metric, selection, or locked-test parameter changed.
- Active Windows power plan: Balanced
- Observed `Sleep after` on AC: `0x00000258` seconds (600 seconds)
- Observed `Hibernate after` on AC: `0x00000000` (disabled)
- `powercfg /requests` could not be read without elevation. No elevation was
  requested or used.

To avoid relying on an unverified Isaac/driver power request during the
multi-day formal campaign, `scripts/pipeline_keep_awake.ps1` was added. It
calls the documented Windows thread execution-state API with
`ES_CONTINUOUS | ES_SYSTEM_REQUIRED` while the exact recorded
full-pipeline-supervisor PID remains alive. It does not change the Windows
power plan and releases the request in `finally`.

## Preserved attempts

1. `pipeline_keep_awake_attempt001` failed before acquiring an execution-state
   request because Windows PowerShell 5.1 interpreted the hexadecimal literal
   `0x80000000` as signed before conversion to `UInt32`. Its stderr is
   preserved at
   `runs/orchestration/full_pipeline_keep_awake_attempt001.stderr.log`.
2. The constant was changed to the exact unsigned decimal representation
   `2147483648`; no runtime or scientific parameter changed.
3. `pipeline_keep_awake_attempt002` started as helper PID `151916`, scoped to
   full-pipeline supervisor PID `162424`. Its first successful status reported
   `ACTIVE`, `native_return=2147483648`, and
   `power_plan_modified=false` in
   `runs/orchestration/full_pipeline_keep_awake_attempt002.json`.

The helper script is included in the method-freeze critical-script inventory
so that its contents cannot drift after locked-test authorization.
