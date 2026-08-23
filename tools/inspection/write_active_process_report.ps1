[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$ReportDir,
    [Parameter(Mandatory)][int]$ObservedLocalTimestep
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$project = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$report = (Resolve-Path $ReportDir).Path
$allowed = (Join-Path $project 'reports\chatgpt_handoff_')
if (-not $report.StartsWith($allowed, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "ReportDir must be an existing reports\chatgpt_handoff_<timestamp> directory under $project"
}
$captured = [DateTime]::UtcNow.ToString('o')
$pattern = 'resume_validation_fsm_residual_ppo|train_residual_ppo|development_gate|full_pipeline_supervisor|formal_training_recovery_supervisor|formal_v34|IsaacLab|wlr_robot|run_until_success\.ps1|pipeline_keep_awake\.ps1|0[56]_train_[BC]\.ps1|isaac-sim|kit\.exe'
$processes = @(Get-CimInstance Win32_Process | Where-Object {
    $_.ProcessId -ne $PID -and $_.CommandLine -and $_.CommandLine -match $pattern
} | ForEach-Object {
    $runtime = Get-Process -Id $_.ProcessId -ErrorAction SilentlyContinue
    [pscustomobject][ordered]@{
        pid = [int]$_.ProcessId
        parent_pid = [int]$_.ParentProcessId
        name = $_.Name
        creation_utc = if ($_.CreationDate) { $_.CreationDate.ToUniversalTime().ToString('o') } else { '' }
        cpu_seconds = if ($runtime) { $runtime.CPU } else { $null }
        working_set_bytes = if ($runtime) { $runtime.WorkingSet64 } else { $null }
        responding = if ($runtime) { $runtime.Responding } else { $null }
        command_line = $_.CommandLine
    }
} | Sort-Object creation_utc)
$cResultPath = Join-Path $project 'runs\ppo_with_com\training\method-C-v34_seed-11_stage-50mm_attempt001\training_result.json'
$cResult = Get-Content -LiteralPath $cResultPath -Raw | ConvertFrom-Json
$checkpointCount = @(Get-ChildItem -LiteralPath (Join-Path (Split-Path $cResultPath) 'checkpoints') -Filter '*.pt' -File -ErrorAction SilentlyContinue).Count
$event = Get-ChildItem -LiteralPath (Split-Path $cResultPath) -Filter 'events.out.tfevents.*' -File | Sort-Object LastWriteTime | Select-Object -Last 1
$supervisorFile = Get-ChildItem -LiteralPath (Join-Path $project 'runs\orchestration') -Filter 'full_pipeline_supervisor_attempt*.json' -File | Sort-Object LastWriteTime | Select-Object -Last 1
$supervisor = Get-Content -LiteralPath $supervisorFile.FullName -Raw | ConvertFrom-Json
$payload = [ordered]@{
    schema = 'resume_validation.read_only_process_audit.v1'
    generated_utc = $captured
    project = $project
    safe_to_start_gui_or_diagnostic = ($processes.Count -eq 0)
    safety_reason = if ($processes.Count) { 'Externally owned training and supervisor processes are active. Do not interrupt; inspection commands must remain DryRun.' } else { 'No matching active process was detected at this snapshot.' }
    destructive_actions_taken = @()
    new_training_or_evaluation_started_by_audit = $false
    locked_test_contents_read = $false
    initial_snapshot = [ordered]@{
        observed_utc = '2026-07-31T21:19:12Z'
        stage = 'development_evaluation'
        controller = 'B'
        seed = 47
        height_mm = 100
        checkpoint = 'final_agent.pt'
        local_timestep = 76800
        heartbeat_path = 'runs\\ppo_without_com\\formal_v34_recovery_attempt002_heartbeat.json'
        heartbeat_hang_detected = $false
        note = 'Initial process check found the externally owned final Method-B development evaluation. It was not interrupted.'
        principal_pids = @(117916,162424,151916,32684,104544,153208,19548,146256)
    }
    final_snapshot = [ordered]@{
        observed_utc = $captured
        supervisor = [ordered]@{ path=$supervisorFile.FullName; attempt=$supervisor.attempt; status=$supervisor.status; updated_utc=$supervisor.updated_utc; live_training_pids=$supervisor.live_training_pids }
        training = [ordered]@{
            stage = 'training'
            method = $cResult.method
            seed = $cResult.seed
            height_mm = $cResult.height_mm
            status = $cResult.status
            run_dir = $cResult.run_dir
            result_path = $cResultPath
            recorded_pid = $cResult.provenance.pid
            observed_local_timestep = $ObservedLocalTimestep
            requested_local_timesteps = $cResult.training_budget.local_timesteps_requested
            checkpoint_count = $checkpointCount
            development_gate_exists = Test-Path -LiteralPath (Join-Path $project "runs\ppo_with_com\development_gates\method-C-v34_seed-11_stage-50mm_attempt001\gate_decision.json")
            event_file = if($event){$event.FullName}else{''}
            event_file_bytes = if($event){$event.Length}else{0}
            event_file_last_write_utc = if($event){$event.LastWriteTimeUtc.ToString('o')}else{''}
            last_update_utc = if($event){$event.LastWriteTimeUtc.ToString('o')}else{''}
            heartbeat_path = ''
            hang_flag = $null
            heartbeat_note = 'No Method-C heartbeat file exists; progress was read from the growing TensorBoard event file and live PID, so hang status is not inferred.'
        }
        processes = $processes
    }
}
$jsonPath = Join-Path $report 'active_processes.json'
[IO.File]::WriteAllText($jsonPath, ($payload | ConvertTo-Json -Depth 12), [Text.UTF8Encoding]::new($false))

$lines = [Collections.Generic.List[string]]::new()
$lines.Add('# Active process status')
$lines.Add('')
$lines.Add("Snapshot UTC: ``$captured``. GUI/diagnostic safe: **$($payload.safe_to_start_gui_or_diagnostic)**.")
$lines.Add('')
$lines.Add('The first audit check found an externally owned Method-B seed-47 / 100 mm final development evaluation at local timestep 76,800. It was not interrupted. By the final snapshot, supervisor attempt 3 had advanced to Method-C seed-11 / 50 mm training.')
$lines.Add('')
$lines.Add("Current Method C state: ``$($cResult.status)``; observed local timestep $ObservedLocalTimestep of $($cResult.training_budget.local_timesteps_requested); $checkpointCount checkpoint files; no development gate. This is an in-progress state, not a performance result.")
$lines.Add('')
$lines.Add('No Method-C heartbeat file exists. Progress was established from the live recorded PID and growing TensorBoard event file; hang status is therefore `unknown`, not `false`.')
$lines.Add('')
$lines.Add("Supervisor: attempt $($supervisor.attempt), status ``$($supervisor.status)``, updated ``$($supervisor.updated_utc)``.")
$lines.Add('')
$lines.Add('## Active processes')
$lines.Add('')
$lines.Add('| PID | Parent | Name | Created UTC | CPU s | Working set bytes | Responding |')
$lines.Add('|---:|---:|---|---|---:|---:|---|')
foreach ($item in $processes) {
    $lines.Add("| $($item.pid) | $($item.parent_pid) | $($item.name) | $($item.creation_utc) | $($item.cpu_seconds) | $($item.working_set_bytes) | $($item.responding) |")
}
$lines.Add('')
$lines.Add('Full command lines (also preserved as structured fields in `active_processes.json`):')
$lines.Add('')
foreach ($item in $processes) {
    $lines.Add("- PID $($item.pid): ``$($item.command_line -replace '`','``')``")
    $lines.Add('')
}
$lines.Add('No process was terminated, suspended, reprioritized, or otherwise modified. No GUI, evaluation, training, validation, or locked test was started by this audit.')
$mdPath = Join-Path $report 'ACTIVE_PROCESS_STATUS.md'
[IO.File]::WriteAllLines($mdPath, $lines, [Text.UTF8Encoding]::new($false))
Write-Host $jsonPath
Write-Host $mdPath
