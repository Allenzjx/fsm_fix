Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$script:ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$script:IsaacLabRoot = 'C:\robotics_sim\IsaacLab'
$script:Evaluator = Join-Path $script:ProjectRoot 'src\resume_validation\evaluate_controller.py'
$script:DevelopmentManifest = Join-Path $script:ProjectRoot 'data\scenario_manifests\development_v2.json'
$condaCommand = Get-Command conda.exe -ErrorAction SilentlyContinue
if (-not $condaCommand) { throw 'conda.exe was not found on PATH; expected the existing env_isaaclab installation.' }
$script:CondaExe = $condaCommand.Source

function Get-InspectionProjectProcesses {
    # A project path by itself is not evidence of an active simulator workload:
    # editors and terminals legitimately open files under ProjectRoot. Require
    # both this exact project root and a known training/evaluation/supervision
    # or inspection-launch entry point so unrelated editors and other IsaacLab
    # projects are never reported as blockers.
    $projectPattern = [regex]::Escape($script:ProjectRoot)
    $workloadPattern = 'train_residual_ppo\.py|evaluate_controller\.py|development_gate|full_pipeline_supervisor\.ps1|formal_training_recovery_supervisor\.ps1|formal_training_monitor\.ps1|run_until_success\.ps1|pipeline_keep_awake\.ps1|0[56]_train_[BC]\.ps1|train_curriculum\.ps1|show_fsm_gui\.ps1|show_ppo_gui\.ps1|show_fsm_vs_ppo\.ps1|open_training_dashboard\.ps1'
    @(Get-CimInstance Win32_Process | Where-Object {
        $_.ProcessId -ne $PID -and $_.CommandLine -and
        $_.CommandLine -match $projectPattern -and
        $_.CommandLine -match $workloadPattern
    } | ForEach-Object {
        $runtime = Get-Process -Id $_.ProcessId -ErrorAction SilentlyContinue
        [pscustomobject]@{
            PID = [int]$_.ProcessId
            ParentPID = [int]$_.ParentProcessId
            Name = $_.Name
            CreationUtc = if ($_.CreationDate) { $_.CreationDate.ToUniversalTime().ToString('o') } else { '' }
            CPUSeconds = if ($runtime) { $runtime.CPU } else { $null }
            WorkingSetBytes = if ($runtime) { $runtime.WorkingSet64 } else { $null }
            Responding = if ($runtime) { $runtime.Responding } else { $null }
            CommandLine = $_.CommandLine
        }
    } | Sort-Object CreationUtc)
}

function Get-InspectionSafety {
    $blockers = @(Get-InspectionProjectProcesses)
    [pscustomobject]@{
        Safe = ($blockers.Count -eq 0)
        Blockers = $blockers
        Reason = if ($blockers.Count) { 'An externally owned training/evaluation/supervisor process is active.' } else { 'No project Isaac/training/evaluation process was detected.' }
    }
}

function Assert-InspectionLaunchSafe {
    $state = Get-InspectionSafety
    if (-not $state.Safe) {
        $pids = ($state.Blockers | ForEach-Object { $_.PID }) -join ', '
        throw "Inspection launch refused: active project process PID(s): $pids. Use -DryRun only and do not interrupt them."
    }
}

function Get-LatestHandoffReport {
    $reports = @(Get-ChildItem -LiteralPath (Join-Path $script:ProjectRoot 'reports') -Directory -Filter 'chatgpt_handoff_*' -ErrorAction SilentlyContinue | Sort-Object Name)
    if (-not $reports.Count) { throw 'No reports\chatgpt_handoff_<timestamp> directory exists.' }
    $reports[-1].FullName
}

function Get-UniqueInspectionOutput {
    param([Parameter(Mandatory)][string]$Label)
    $stamp = Get-Date -Format 'yyyyMMdd_HHmmss_fff'
    Join-Path (Get-LatestHandoffReport) (Join-Path 'gui_runs' "${Label}_${stamp}")
}

function Get-ManifestScenarios {
    $manifest = Get-Content -LiteralPath $script:DevelopmentManifest -Raw | ConvertFrom-Json
    @($manifest.scenarios)
}

function Resolve-InspectionScenario {
    param(
        [Parameter(Mandatory)][ValidateSet(50,75,100)][int]$HeightMm,
        [string]$ScenarioId,
        [Parameter(Mandatory)][ValidateSet('nominal','development-success','development-failure')][string]$ScenarioMode,
        [string]$EvidenceEpisodes
    )
    $heightScenarios = @(Get-ManifestScenarios | Where-Object { [int][math]::Round([double]$_.obstacle_height_m * 1000) -eq $HeightMm })
    if ($ScenarioId) {
        $matched = @($heightScenarios | Where-Object { $_.scenario_id -eq $ScenarioId })
        if ($matched.Count -ne 1) { throw "Scenario '$ScenarioId' does not occur exactly once in the $HeightMm mm development split." }
        return $ScenarioId
    }
    if ($ScenarioMode -eq 'nominal') {
        $selected = $heightScenarios | Sort-Object @{ Expression = {
            [math]::Abs([double]$_.initial_distance_m - 0.25) +
            0.25 * [math]::Abs([double]$_.friction - 1.0) +
            2.0 * [math]::Abs([double]$_.initial_pitch_rad) +
            0.01 * [double]$_.actuator_delay_steps +
            5.0 * [double]$_.sensor_noise_std
        }} | Select-Object -First 1
        if (-not $selected) { throw "No $HeightMm mm development scenario was found." }
        return [string]$selected.scenario_id
    }
    if (-not $EvidenceEpisodes -or -not (Test-Path -LiteralPath $EvidenceEpisodes -PathType Leaf)) {
        throw "ScenarioMode '$ScenarioMode' requires an existing controller episodes.jsonl; no controller fallback is allowed."
    }
    $wantSuccess = $ScenarioMode -eq 'development-success'
    $selectedEpisode = Get-Content -LiteralPath $EvidenceEpisodes | ForEach-Object { $_ | ConvertFrom-Json } |
        Where-Object { [bool]$_.success -eq $wantSuccess } | Select-Object -First 1
    if (-not $selectedEpisode) { throw "No '$ScenarioMode' episode exists in $EvidenceEpisodes." }
    return [string]$selectedEpisode.scenario_id
}

function Get-FsmEvidenceEpisodes {
    param([Parameter(Mandatory)][ValidateSet(50,75,100)][int]$HeightMm)
    $names = @{
        50 = 'development_50mm_current_config_attempt043'
        75 = 'development_75mm_formal_full_attempt042'
        100 = 'development_100mm_current_config_attempt044'
    }
    Join-Path $script:ProjectRoot "runs\fsm\$($names[$HeightMm])\episodes.jsonl"
}

function Get-FormalControllerRun {
    param(
        [Parameter(Mandatory)][ValidateSet('B','C')][string]$Method,
        [Parameter(Mandatory)][int]$Seed,
        [Parameter(Mandatory)][ValidateSet(50,75,100)][int]$HeightMm,
        [switch]$RequireCompleted
    )
    $folder = if ($Method -eq 'B') { 'ppo_without_com' } else { 'ppo_with_com' }
    $root = Join-Path $script:ProjectRoot "runs\$folder\training"
    $regex = "^method-$Method-v\d+_seed-$Seed`_stage-$HeightMm`mm_attempt(\d+)$"
    $records = @(Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue | Where-Object Name -Match $regex | ForEach-Object {
        $resultPath = Join-Path $_.FullName 'training_result.json'
        $result = if (Test-Path -LiteralPath $resultPath) { Get-Content -LiteralPath $resultPath -Raw | ConvertFrom-Json } else { $null }
        [pscustomobject]@{ Directory=$_.FullName; Name=$_.Name; Attempt=[int]$Matches[1]; Result=$result; Folder=$folder }
    } | Where-Object { -not $RequireCompleted -or ($_.Result -and $_.Result.status -eq 'COMPLETED') } | Sort-Object Attempt)
    if (-not $records.Count) {
        $qualifier = if ($RequireCompleted) { 'completed ' } else { '' }
        throw "No ${qualifier}Method $Method run exists for seed $Seed / $HeightMm mm. No checkpoint fallback is permitted."
    }
    $records[-1]
}

function Format-InspectionCommand {
    param([Parameter(Mandatory)][string[]]$Arguments)
    ($Arguments | ForEach-Object { if ($_ -match '[\s`"'']') { "'" + ($_ -replace "'", "''") + "'" } else { $_ } }) -join ' '
}

function Get-Sha256Lower {
    param([Parameter(Mandatory)][string]$Path)
    (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}
