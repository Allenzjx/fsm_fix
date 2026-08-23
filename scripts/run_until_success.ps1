[CmdletBinding()]
param(
    [string]$RuntimeVersion = "v34",
    [int]$ValidationAttempt = 1,
    [int]$VideoSmokeAttempt = 1,
    [int]$LockedAttempt = 1,
    [int]$VideoAttempt = 1,
    [ValidateRange(1, 120)]
    [int]$LockedRecordStride = 10,
    [bool]$ContinueAfterFailedDevelopmentGate = $true,
    [switch]$RecheckFoundations,
    [switch]$StopAfterTraining
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = "C:\Users\kskzz\miniconda3\envs\env_isaaclab\python.exe"
$OrchestrationRoot = Join-Path $ProjectRoot "runs\orchestration"
$StatePath = Join-Path $OrchestrationRoot "run_until_success_state.json"
$InvocationId = (
    "run-until-success_{0}_{1}" -f
    (Get-Date -Format "yyyyMMdd_HHmmss"),
    ([Guid]::NewGuid().ToString("N").Substring(0, 8))
)
$InvocationRoot = Join-Path $OrchestrationRoot $InvocationId
$EventLog = Join-Path $InvocationRoot "stage_events.jsonl"

New-Item -ItemType Directory -Path $InvocationRoot -Force | Out-Null

$StageOrder = @(
    "INVENTORY",
    "UNIT_TEST",
    "ASSET_VALIDATION",
    "SENSOR_VALIDATION",
    "REPLAY_VALIDATION",
    "FSM_DEVELOPMENT",
    "FSM_VALIDATION",
    "PPO_NO_COM_SMOKE",
    "PPO_COM_SMOKE",
    "PPO_NO_COM_DEVELOPMENT",
    "PPO_COM_DEVELOPMENT",
    "MULTI_SEED_REPRODUCTION",
    "PREVALIDATION_VIDEO_SMOKE",
    "METHOD_FREEZE",
    "LOCKED_TEST",
    "REPORT",
    "COMPLETE"
)

function Write-JsonAtomic {
    param(
        [Parameter(Mandatory = $true)]$Payload,
        [Parameter(Mandatory = $true)][string]$Path
    )
    $Directory = Split-Path -Parent $Path
    New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    $Temporary = Join-Path $Directory (
        ".{0}.{1}.tmp" -f
        (Split-Path -Leaf $Path),
        ([Guid]::NewGuid().ToString("N"))
    )
    $Payload | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $Temporary -Encoding UTF8
    Move-Item -LiteralPath $Temporary -Destination $Path -Force
}

function Write-StageEvent {
    param(
        [Parameter(Mandatory = $true)][string]$Stage,
        [Parameter(Mandatory = $true)][string]$Status,
        [Parameter(Mandatory = $true)][string]$Hypothesis,
        [Parameter(Mandatory = $true)][string]$Result,
        [Parameter(Mandatory = $true)][string]$NextAction,
        [string[]]$ChangedParameters = @(),
        [string[]]$UnchangedControls = @(),
        [string[]]$Evidence = @()
    )
    $Event = [ordered]@{
        schema = "resume_validation.orchestration_stage_event.v1"
        experiment_id = "$InvocationId/$Stage"
        parent_experiment_id = $InvocationId
        timestamp_utc = (Get-Date).ToUniversalTime().ToString("o")
        stage = $Stage
        status = $Status
        hypothesis = $Hypothesis
        changed_parameters = @($ChangedParameters)
        unchanged_controls = @($UnchangedControls)
        expected_effect = "Advance only when the stage's recorded evidence passes its existing gate."
        actual_effect = $Result
        result = $Status
        next_action = $NextAction
        evidence = @($Evidence)
    }
    ($Event | ConvertTo-Json -Depth 20 -Compress) |
        Add-Content -LiteralPath $EventLog -Encoding UTF8

    $PreviousHistory = @()
    if (Test-Path -LiteralPath $StatePath -PathType Leaf) {
        try {
            $Previous = Get-Content -LiteralPath $StatePath -Raw | ConvertFrom-Json
            $PreviousHistory = @($Previous.history)
        } catch {
            throw "Orchestration state is unreadable; preserve it for diagnosis: $StatePath"
        }
    }
    $HistoryEntry = [ordered]@{
        invocation_id = $InvocationId
        stage = $Stage
        status = $Status
        timestamp_utc = $Event.timestamp_utc
        result = $Result
        evidence = @($Evidence)
    }
    $History = @($PreviousHistory + $HistoryEntry)
    if ($History.Count -gt 500) {
        $History = @($History | Select-Object -Last 500)
    }
    $State = [ordered]@{
        schema = "resume_validation.run_until_success_state.v1"
        updated_utc = $Event.timestamp_utc
        invocation_id = $InvocationId
        stage_order = $StageOrder
        current_stage = $Stage
        status = $Status
        result = $Result
        next_action = $NextAction
        event_log = $EventLog
        history = $History
    }
    Write-JsonAtomic -Payload $State -Path $StatePath
}

function Assert-LastExitCode {
    param([string]$Action)
    if ($LASTEXITCODE -ne 0) {
        throw "$Action failed with exit code $LASTEXITCODE"
    }
}

function Invoke-ProjectScript {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [object[]]$Arguments = @()
    )
    $Path = Join-Path $PSScriptRoot $Name
    # Array splatting into a PowerShell script is positional: strings such as
    # "-Attempt" are otherwise bound to the first declared parameter. Launch a
    # child PowerShell command line so the script binder interprets the names.
    $InvocationArguments = @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", $Path
    ) + @($Arguments)
    & powershell.exe @InvocationArguments
    $ProjectScriptExitCode = $LASTEXITCODE
    if ($ProjectScriptExitCode -ne 0) {
        throw "$Name exited with code $ProjectScriptExitCode"
    }
}

function Get-RequiredCoreReportNames {
    return @(
        "locked_test_report.md",
        "claims_audit.md",
        "final_resume_wording_zh.md",
        "resume_metrics.json",
        "failure_analysis.md",
        "unit_test_results.xml"
    )
}

function Get-RequiredReportNames {
    return @(
        (Get-RequiredCoreReportNames)
        "final_audit.json"
        "final_audit.md"
    )
}

function Test-CorePublishedReports {
    $ReportsRoot = Join-Path $ProjectRoot "reports"
    foreach ($Name in Get-RequiredCoreReportNames) {
        if (-not (Test-Path -LiteralPath (Join-Path $ReportsRoot $Name) -PathType Leaf)) {
            return $false
        }
    }
    try {
        $UnitAudit = [xml](Get-Content -LiteralPath (
            Join-Path $ReportsRoot "unit_test_results.xml"
        ) -Raw)
        $Suites = @($UnitAudit.testsuites.testsuite)
        $TestCount = ($Suites | Measure-Object -Property tests -Sum).Sum
        $FailureCount = ($Suites | Measure-Object -Property failures -Sum).Sum
        $ErrorCount = ($Suites | Measure-Object -Property errors -Sum).Sum
        if (
            [int]$TestCount -lt 1 -or
            [int]$FailureCount -ne 0 -or
            [int]$ErrorCount -ne 0
        ) {
            return $false
        }
        $Metrics = Get-Content -LiteralPath (
            Join-Path $ReportsRoot "resume_metrics.json"
        ) -Raw | ConvertFrom-Json
        if (
            [string]::IsNullOrWhiteSpace([string]$Metrics.protocol_version) -or
            [string]::IsNullOrWhiteSpace([string]$Metrics.locked_test_manifest_sha256) -or
            $null -eq $Metrics.methods -or
            [int]$Metrics.unit_test_audit.tests -ne [int]$TestCount -or
            [int]$Metrics.video_evidence.video_count -lt 1
        ) {
            return $false
        }
    } catch {
        return $false
    }
    return $true
}

function Test-PublishedReports {
    if (-not (Test-CorePublishedReports)) {
        return $false
    }
    $ReportsRoot = Join-Path $ProjectRoot "reports"
    $FinalAuditPath = Join-Path $ReportsRoot "final_audit.json"
    $FinalAuditMarkdown = Join-Path $ReportsRoot "final_audit.md"
    if (
        -not (Test-Path -LiteralPath $FinalAuditPath -PathType Leaf) -or
        -not (Test-Path -LiteralPath $FinalAuditMarkdown -PathType Leaf)
    ) {
        return $false
    }
    try {
        $FinalAudit = Get-Content -LiteralPath $FinalAuditPath -Raw |
            ConvertFrom-Json
        $FreezePath = Join-Path $ProjectRoot "configs\method_freeze.json"
        if (
            $FinalAudit.schema -ne "resume_validation.final_delivery_audit.v1" -or
            $FinalAudit.status -notin @("PASS", "PASS_WITH_DISCLOSURES") -or
            $FinalAudit.method_freeze_sha256 -ne
            (Get-FileHash -LiteralPath $FreezePath -Algorithm SHA256).Hash.ToLowerInvariant()
        ) {
            return $false
        }
    } catch {
        return $false
    }
    return $true
}

function Test-FoundationFreeze {
    $FreezePath = Join-Path $ProjectRoot "configs\config_freeze.json"
    if (-not (Test-Path -LiteralPath $FreezePath -PathType Leaf)) {
        return $false
    }
    $Freeze = Get-Content -LiteralPath $FreezePath -Raw | ConvertFrom-Json
    foreach ($Name in @("fsm", "metrics")) {
        $RelativePath = [string]$Freeze.frozen."${Name}_path"
        $ExpectedHash = [string]$Freeze.frozen."${Name}_sha256"
        $Path = Join-Path $ProjectRoot $RelativePath
        if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
            return $false
        }
        $ActualHash = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($ActualHash -ne $ExpectedHash) {
            return $false
        }
    }
    foreach ($Property in $Freeze.development_evidence.PSObject.Properties) {
        $Path = Join-Path $ProjectRoot ([string]$Property.Value.path)
        if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
            return $false
        }
        $ActualHash = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($ActualHash -ne [string]$Property.Value.sha256) {
            return $false
        }
    }
    return $true
}

function Get-FormalRuns {
    param([ValidateSet("B", "C")][string]$Method)
    $MethodFolder = if ($Method -eq "B") { "ppo_without_com" } else { "ppo_with_com" }
    $TrainingRoot = Join-Path $ProjectRoot "runs\$MethodFolder\training"
    $Records = @()
    if (-not (Test-Path -LiteralPath $TrainingRoot -PathType Container)) {
        return @()
    }
    $Pattern = "method-$Method-$RuntimeVersion`_seed-*_stage-*mm_attempt*"
    foreach ($Directory in Get-ChildItem -LiteralPath $TrainingRoot -Directory -Filter $Pattern) {
        if ($Directory.Name -notmatch (
            "^method-$Method-$([regex]::Escape($RuntimeVersion))_seed-(11|29|47)" +
            "_stage-(50|75|100)mm_attempt(\d{3,})$"
        )) {
            continue
        }
        $ResultPath = Join-Path $Directory.FullName "training_result.json"
        $Status = "MISSING_TRAINING_RESULT"
        $Payload = $null
        if (Test-Path -LiteralPath $ResultPath -PathType Leaf) {
            $Payload = Get-Content -LiteralPath $ResultPath -Raw | ConvertFrom-Json
            $Status = [string]$Payload.status
        }
        $Records += [PSCustomObject]@{
            method = $Method
            seed = [int]$Matches[1]
            height_mm = [int]$Matches[2]
            attempt = [int]$Matches[3]
            run_name = $Directory.Name
            run_dir = $Directory.FullName
            result_path = $ResultPath
            status = $Status
            pid = if ($null -ne $Payload) { [int]$Payload.provenance.pid } else { 0 }
            final_checkpoint = Join-Path $Directory.FullName "checkpoints\final_agent.pt"
        }
    }
    return @($Records)
}

function Get-LiveFormalRuns {
    param([object[]]$Runs)
    $Live = @()
    foreach ($Run in @($Runs | Where-Object { $_.status -eq "RUNNING" })) {
        if ($Run.pid -gt 0) {
            $Process = Get-CimInstance Win32_Process -Filter (
                "ProcessId = $($Run.pid)"
            ) -ErrorAction SilentlyContinue
            if (
                $null -ne $Process -and
                $Process.Name -eq "python.exe" -and
                $Process.CommandLine -like "*train_residual_ppo.py*" -and
                $Process.CommandLine -like "*$($Run.run_name)*"
            ) {
                $Live += $Run
            }
        }
    }
    return @($Live)
}

function Get-CompletedStage {
    param(
        [object[]]$Runs,
        [int]$Seed,
        [int]$Height
    )
    $Candidates = @(
        $Runs |
            Where-Object {
                $_.seed -eq $Seed -and
                $_.height_mm -eq $Height -and
                $_.status -eq "COMPLETED" -and
                (Test-Path -LiteralPath $_.final_checkpoint -PathType Leaf)
            } |
            Sort-Object attempt, run_name
    )
    if ($Candidates.Count -eq 0) {
        return $null
    }
    # Curriculum recovery uses the most recent completed attempt, never a
    # development or validation performance score.
    return $Candidates[-1]
}

function Invoke-MissingTrainingCoverage {
    param([ValidateSet("B", "C")][string]$Method)
    $Runs = @(Get-FormalRuns -Method $Method)
    $Live = @(Get-LiveFormalRuns -Runs $Runs)
    if ($Live.Count -gt 0) {
        $Names = ($Live | ForEach-Object { "$($_.run_name) pid=$($_.pid)" }) -join ", "
        Write-StageEvent `
            -Stage "MULTI_SEED_REPRODUCTION" `
            -Status "WAITING" `
            -Hypothesis "The already-running formal process will continue producing registered checkpoints." `
            -Result "A live formal training process exists; no duplicate process was launched: $Names" `
            -NextAction "Wait for the live process, then invoke this state machine again." `
            -UnchangedControls @("runtime=$RuntimeVersion", "seeds=11,29,47", "heights=50,75,100")
        Write-Output "Formal training is already active: $Names"
        exit 3
    }

    $FirstMissing = $null
    foreach ($Seed in @(11, 29, 47)) {
        foreach ($Height in @(50, 75, 100)) {
            if ($null -eq (Get-CompletedStage -Runs $Runs -Seed $Seed -Height $Height)) {
                $FirstMissing = [PSCustomObject]@{ seed = $Seed; height_mm = $Height }
                break
            }
        }
        if ($null -ne $FirstMissing) {
            break
        }
    }
    if ($null -eq $FirstMissing) {
        return
    }

    $ResumeCheckpoint = ""
    if ($FirstMissing.height_mm -ne 50) {
        $PriorHeight = if ($FirstMissing.height_mm -eq 75) { 50 } else { 75 }
        $Prior = Get-CompletedStage -Runs $Runs -Seed $FirstMissing.seed -Height $PriorHeight
        if ($null -eq $Prior) {
            throw (
                "Non-contiguous curriculum evidence for method ${Method}: " +
                "seed=$($FirstMissing.seed), missing prior ${PriorHeight}mm stage"
            )
        }
        $ResumeCheckpoint = $Prior.final_checkpoint
    }
    $MaximumAttempt = 0
    if ($Runs.Count -gt 0) {
        $MaximumAttempt = [int](($Runs | Measure-Object -Property attempt -Maximum).Maximum)
    }
    $RecoveryAttempt = [Math]::Max(1, $MaximumAttempt + 1)
    $Wrapper = if ($Method -eq "B") { "05_train_B.ps1" } else { "06_train_C.ps1" }
    $Arguments = @(
        "-Attempt", $RecoveryAttempt,
        "-RuntimeVersion", $RuntimeVersion,
        "-StartSeed", $FirstMissing.seed,
        "-StartHeight", $FirstMissing.height_mm,
        "-ContinueAfterFailedGate"
    )
    if (-not [string]::IsNullOrWhiteSpace($ResumeCheckpoint)) {
        $Arguments += @("-InitialResumeCheckpoint", $ResumeCheckpoint)
    }
    if (-not $ContinueAfterFailedDevelopmentGate) {
        $Arguments = @($Arguments | Where-Object { $_ -ne "-ContinueAfterFailedGate" })
    }
    Write-StageEvent `
        -Stage "MULTI_SEED_REPRODUCTION" `
        -Status "RUNNING" `
        -Hypothesis "A new immutable attempt can fill the first missing formal curriculum stage without reusing failed output." `
        -Result (
            "Launching method $Method at seed=$($FirstMissing.seed), " +
            "height=$($FirstMissing.height_mm)mm, attempt=$RecoveryAttempt."
        ) `
        -NextAction "Run the remaining fixed schedule, then re-audit complete coverage." `
        -ChangedParameters @(
            "attempt=$RecoveryAttempt",
            "start_seed=$($FirstMissing.seed)",
            "start_height_mm=$($FirstMissing.height_mm)"
        ) `
        -UnchangedControls @(
            "runtime=$RuntimeVersion",
            "local_timesteps_per_stage=76800",
            "num_envs=64",
            "rollouts=64",
            "seeds=11,29,47",
            "heights=50,75,100"
        ) `
        -Evidence @($ResumeCheckpoint)
    Invoke-ProjectScript -Name $Wrapper -Arguments $Arguments

    $After = @(Get-FormalRuns -Method $Method)
    foreach ($Seed in @(11, 29, 47)) {
        foreach ($Height in @(50, 75, 100)) {
            if ($null -eq (Get-CompletedStage -Runs $After -Seed $Seed -Height $Height)) {
                throw "Training wrapper returned without complete coverage: method=$Method seed=$Seed height=${Height}mm"
            }
        }
    }
}

function Invoke-FormalSmoke {
    param([ValidateSet("B", "C")][string]$Method)
    $MethodFolder = if ($Method -eq "B") { "ppo_without_com" } else { "ppo_with_com" }
    $Stage = if ($Method -eq "B") {
        "PPO_NO_COM_SMOKE"
    } else {
        "PPO_COM_SMOKE"
    }
    $OutputRoot = Join-Path $ProjectRoot "runs\$MethodFolder\training"
    New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null
    $Pattern = "method-$Method-$RuntimeVersion`_seed-11_stage-50mm_smoke_attempt*"
    $Existing = @(
        Get-ChildItem -LiteralPath $OutputRoot -Directory -Filter $Pattern |
            Sort-Object Name
    )
    foreach ($Directory in $Existing) {
        $ResultPath = Join-Path $Directory.FullName "training_result.json"
        if (Test-Path -LiteralPath $ResultPath -PathType Leaf) {
            $Result = Get-Content -LiteralPath $ResultPath -Raw | ConvertFrom-Json
            $SmokeValid = (
                $Result.status -eq "SMOKE_PASS" -and
                $Result.method -eq $Method -and
                [int]$Result.seed -eq 11 -and
                [int]$Result.height_mm -eq 50
            )
            if ($SmokeValid) {
                $AssetPath = [string]$Result.provenance.asset_path
                $SmokeValid = (
                    (Test-Path -LiteralPath $AssetPath -PathType Leaf) -and
                    (Get-FileHash -LiteralPath $AssetPath -Algorithm SHA256).Hash.ToLowerInvariant() -eq
                    [string]$Result.provenance.asset_sha256
                )
            }
            if ($SmokeValid) {
                foreach ($Entry in @(
                    $Result.provenance.configs.PSObject.Properties.Value
                    $Result.provenance.source_files.PSObject.Properties.Value
                )) {
                    if (
                        -not (Test-Path -LiteralPath ([string]$Entry.path) -PathType Leaf) -or
                        (Get-FileHash -LiteralPath ([string]$Entry.path) -Algorithm SHA256).Hash.ToLowerInvariant() -ne
                        [string]$Entry.sha256
                    ) {
                        $SmokeValid = $false
                        break
                    }
                }
            }
            if ($SmokeValid) {
                Write-StageEvent `
                    -Stage $Stage `
                    -Status "COMPLETED" `
                    -Hypothesis "The registered runtime has finite observations/rewards and physically realizes bounded residual commands." `
                    -Result "Verified preserved SMOKE_PASS for method $Method." `
                    -NextAction "Run or recover the fixed formal curriculum." `
                    -Evidence @($ResultPath)
                return
            }
        }
    }
    $Attempt = $Existing.Count + 1
    while ($true) {
        $RunName = (
            "method-$Method-$RuntimeVersion`_seed-11_stage-50mm_" +
            "smoke_attempt$('{0:D3}' -f $Attempt)"
        )
        $RunDir = Join-Path $OutputRoot $RunName
        if (-not (Test-Path -LiteralPath $RunDir)) {
            break
        }
        $Attempt += 1
    }
    Write-StageEvent `
        -Stage $Stage -Status "RUNNING" `
        -Hypothesis "Method $Method passes the same real-Isaac distribution, zero-action, reward, projection, IK, and actuator realization smoke." `
        -Result "Launching immutable smoke attempt $Attempt." `
        -NextAction "Require SMOKE_PASS before formal curriculum launch." `
        -ChangedParameters @("method=$Method", "smoke_attempt=$Attempt") `
        -UnchangedControls @(
            "runtime=$RuntimeVersion",
            "seed=11",
            "height_mm=50",
            "num_envs=64",
            "asset/FSM/metrics/PPO architecture frozen"
        )
    $IsaacLabRoot = "C:\robotics_sim\IsaacLab"
    $Trainer = Join-Path $ProjectRoot "src\resume_validation\train_residual_ppo.py"
    Push-Location $IsaacLabRoot
    try {
        & conda run --no-capture-output -n env_isaaclab .\isaaclab.bat -p $Trainer `
            --method $Method `
            --seed 11 `
            --height_mm 50 `
            --num_envs 64 `
            --run_name $RunName `
            --output_root $OutputRoot `
            --smoke_only `
            --headless
        Assert-LastExitCode -Action "method $Method real-Isaac smoke"
    } finally {
        Pop-Location
    }
    $ResultPath = Join-Path $RunDir "training_result.json"
    if (-not (Test-Path -LiteralPath $ResultPath -PathType Leaf)) {
        throw "Method $Method smoke produced no training_result.json"
    }
    $Result = Get-Content -LiteralPath $ResultPath -Raw | ConvertFrom-Json
    if ($Result.status -ne "SMOKE_PASS") {
        throw "Method $Method smoke failed: $ResultPath"
    }
    Write-StageEvent `
        -Stage $Stage -Status "COMPLETED" `
        -Hypothesis "Method $Method passes real-Isaac preflight and physical residual realization." `
        -Result "SMOKE_PASS." `
        -NextAction "Run the fixed formal curriculum." `
        -Evidence @($ResultPath)
}

try {
    $FoundationFrozen = Test-FoundationFreeze
    if ($RecheckFoundations -or -not $FoundationFrozen) {
        Write-StageEvent `
            -Stage "INVENTORY" -Status "RUNNING" `
            -Hypothesis "Local sources, asset inputs, replay inputs, and unit behavior remain auditable." `
            -Result "Launching inventory, source audit, replay parsing, and unit regression." `
            -NextAction "Validate the Isaac asset." `
            -UnchangedControls @("project_root=$ProjectRoot")
        Invoke-ProjectScript -Name "00_inventory.ps1"
        Write-StageEvent `
            -Stage "UNIT_TEST" -Status "COMPLETED" `
            -Hypothesis "Pure-Python inventory, replay, configuration, control, metric, statistics, and manifest regressions pass." `
            -Result "The inventory runner returned successfully after its unit regression." `
            -NextAction "Validate the Isaac asset."

        Write-StageEvent `
            -Stage "ASSET_VALIDATION" -Status "RUNNING" `
            -Hypothesis "The derived USD loads, settles, and accepts mapped actuator commands in Isaac." `
            -Result "Launching fresh static and motion integration." `
            -NextAction "Validate sensors and the residual environment."
        Invoke-ProjectScript -Name "01_validate_asset.ps1"
        Write-StageEvent `
            -Stage "ASSET_VALIDATION" -Status "COMPLETED" `
            -Hypothesis "The derived USD loads, settles, and accepts mapped actuator commands." `
            -Result "Fresh Isaac asset integration returned successfully." `
            -NextAction "Validate sensors and the residual environment."

        Write-StageEvent `
            -Stage "SENSOR_VALIDATION" -Status "RUNNING" `
            -Hypothesis "Contact, observation, zero-residual, random-residual, and runtime FK checks pass." `
            -Result "Launching fresh residual-environment and FK validation." `
            -NextAction "Replay the raw 50/100 mm references."
        Invoke-ProjectScript -Name "02_validate_sensors_and_residual_env.ps1"
        Write-StageEvent `
            -Stage "SENSOR_VALIDATION" -Status "COMPLETED" `
            -Hypothesis "Sensors, zero/random residual behavior, vectorized stepping, and runtime FK are finite and consistent." `
            -Result "Fresh residual-environment and runtime-FK checks returned successfully." `
            -NextAction "Replay raw references."

        Write-StageEvent `
            -Stage "REPLAY_VALIDATION" -Status "RUNNING" `
            -Hypothesis "The recorded command timing executes through the same DirectRLEnv chain." `
            -Result "Launching fresh replay validation." `
            -NextAction "Verify or develop the FSM."
        Invoke-ProjectScript -Name "03_replay_50mm_100mm.ps1"
        Write-StageEvent `
            -Stage "REPLAY_VALIDATION" -Status "COMPLETED" `
            -Hypothesis "Raw replay timing executes through the formal DirectRLEnv path." `
            -Result "Fresh replay runner returned successfully." `
            -NextAction "Verify the frozen FSM development evidence."

        if (-not (Test-FoundationFreeze)) {
            Write-StageEvent `
                -Stage "FSM_DEVELOPMENT" -Status "BLOCKED" `
                -Hypothesis "FSM development evidence must be selected and frozen before PPO training." `
                -Result "The frozen FSM/metrics manifest is absent, drifted, or references invalid evidence." `
                -NextAction "Run documented FSM development, select on development data only, and create configs/config_freeze.json."
            throw "FSM/metrics development freeze is not valid; formal training is not authorized"
        }
    }
    Write-StageEvent `
        -Stage "FSM_VALIDATION" -Status "COMPLETED" `
        -Hypothesis "Frozen FSM and metric hashes still match their recorded development evidence." `
        -Result "Configuration freeze and every referenced development-evidence hash verified." `
        -NextAction "Complete both formal residual-PPO schedules." `
        -Evidence @((Join-Path $ProjectRoot "configs\config_freeze.json"))

    if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot "configs\method_freeze.json"))) {
        Invoke-FormalSmoke -Method "B"
        Invoke-MissingTrainingCoverage -Method "B"
        Write-StageEvent `
            -Stage "PPO_NO_COM_DEVELOPMENT" -Status "COMPLETED" `
            -Hypothesis "Method B has complete formal coverage for all registered seeds and heights." `
            -Result "At least one immutable COMPLETED stage-final checkpoint exists in every B stratum." `
            -NextAction "Complete Method C."

        Invoke-FormalSmoke -Method "C"
        Invoke-MissingTrainingCoverage -Method "C"
        Write-StageEvent `
            -Stage "PPO_COM_DEVELOPMENT" -Status "COMPLETED" `
            -Hypothesis "Method C has complete formal coverage for all registered seeds and heights." `
            -Result "At least one immutable COMPLETED stage-final checkpoint exists in every C stratum." `
            -NextAction "Run the frozen validation-selection protocol."

        if ($StopAfterTraining) {
            Write-Output "Formal training coverage is complete; stopped before validation by request."
            exit 0
        }

        Write-StageEvent `
            -Stage "MULTI_SEED_REPRODUCTION" -Status "COMPLETED" `
            -Hypothesis "B and C both retain all 3 seeds x 3 heights." `
            -Result "Complete formal checkpoint coverage verified without best-seed filtering." `
            -NextAction "Validate the real camera/encoder path, then evaluate every completed candidate on validation_v2."

        Write-StageEvent `
            -Stage "PREVALIDATION_VIDEO_SMOKE" -Status "RUNNING" `
            -Hypothesis "The exact single-scenario evaluator can render diagnostic overlays and encode a real MP4 before source freeze." `
            -Result "Launching one development-scenario physical camera smoke; no locked data is used." `
            -NextAction "Require the video/result/episode hash chain before validation and method freeze."
        Invoke-ProjectScript -Name "prevalidation_video_smoke.ps1" -Arguments @(
            "-Attempt", $VideoSmokeAttempt
        )
        Write-StageEvent `
            -Stage "PREVALIDATION_VIDEO_SMOKE" -Status "COMPLETED" `
            -Hypothesis "The physical camera, overlay, and encoder path produces immutable real-Isaac evidence." `
            -Result "Development-scenario result, episode, telemetry, status, and MP4 hash checks passed." `
            -NextAction "Run validation selection and include the smoke evidence in method freeze."

        Invoke-ProjectScript -Name "07_run_validation.ps1" -Arguments @(
            "-RuntimeVersion", $RuntimeVersion,
            "-ValidationAttempt", $ValidationAttempt
        )

        Write-StageEvent `
            -Stage "METHOD_FREEZE" -Status "RUNNING" `
            -Hypothesis "Raw validation episodes reproduce every summary and deterministic selection." `
            -Result "Launching independent recomputation and method freeze." `
            -NextAction "Verify the freeze, then authorize the first locked-manifest access."
        Invoke-ProjectScript -Name "08_freeze_methods.ps1" -Arguments @(
            "-RuntimeVersion", $RuntimeVersion,
            "-ValidationAttempt", $ValidationAttempt
        )
    }

    $MethodFreeze = Join-Path $ProjectRoot "configs\method_freeze.json"
    $PreviousPythonPath = $env:PYTHONPATH
    $SourceRoot = Join-Path $ProjectRoot "src"
    $env:PYTHONPATH = if ([string]::IsNullOrWhiteSpace($PreviousPythonPath)) {
        $SourceRoot
    } else {
        "$SourceRoot$([IO.Path]::PathSeparator)$PreviousPythonPath"
    }
    try {
        & $Python -m resume_validation.method_freeze verify --freeze $MethodFreeze
        Assert-LastExitCode -Action "method-freeze verification"
    } finally {
        $env:PYTHONPATH = $PreviousPythonPath
    }
    Write-StageEvent `
        -Stage "METHOD_FREEZE" -Status "COMPLETED" `
        -Hypothesis "Frozen methods, checkpoints, source hashes, and validation evidence have not drifted." `
        -Result "Independent method-freeze verification passed." `
        -NextAction "Run the paired locked test exactly once per registered stratum." `
        -Evidence @($MethodFreeze)

    if (Test-PublishedReports) {
        Write-StageEvent `
            -Stage "COMPLETE" -Status "COMPLETED" `
            -Hypothesis "A recoverable rerun must verify and reuse already-published immutable final evidence." `
            -Result "All required reports, schema checks, and passing unit-test totals remain valid; no output was overwritten." `
            -NextAction "Use only the audited wording and values in reports/final_resume_wording_zh.md." `
            -Evidence @(
                (Get-RequiredReportNames) |
                    ForEach-Object { Join-Path $ProjectRoot "reports\$_" }
            )
        Write-Output "COMPLETE (verified existing evidence): $ProjectRoot"
        exit 0
    }

    Write-StageEvent `
        -Stage "LOCKED_TEST" -Status "RUNNING" `
        -Hypothesis "FSM/B/C will be evaluated on identical frozen scenarios with complete paired coverage." `
        -Result "Launching or recovering the frozen locked campaign." `
        -NextAction "Audit all 2,100 episode records before selecting video replays."
    Invoke-ProjectScript -Name "09_run_locked_test.ps1" -Arguments @(
        "-RuntimeVersion", $RuntimeVersion,
        "-LockedAttempt", $LockedAttempt,
        "-RecordStride", $LockedRecordStride
    )
    Write-StageEvent `
        -Stage "LOCKED_TEST" -Status "COMPLETED" `
        -Hypothesis "FSM/B/C are evaluated on identical frozen scenarios with complete paired coverage." `
        -Result "Locked-test runner and its paired-coverage audit completed." `
        -NextAction "Replay deterministic video evidence and generate reports."

    Write-StageEvent `
        -Stage "REPORT" -Status "RUNNING" `
        -Hypothesis "Deterministic locked-episode replays and raw paired data can publish every required evidence artifact." `
        -Result "Launching video replay, unit regression, statistics, claims audit, and report publication." `
        -NextAction "Verify final schemas, files, and zero test failures."
    Invoke-ProjectScript -Name "10_generate_videos.ps1" -Arguments @(
        "-RuntimeVersion", $RuntimeVersion,
        "-LockedAttempt", $LockedAttempt,
        "-VideoAttempt", $VideoAttempt
    )
    if (-not (Test-CorePublishedReports)) {
        Invoke-ProjectScript -Name "11_generate_report.ps1" -Arguments @(
            "-RuntimeVersion", $RuntimeVersion,
            "-LockedAttempt", $LockedAttempt,
            "-VideoAttempt", $VideoAttempt
        )
    }
    Invoke-ProjectScript -Name "12_final_audit.ps1" -Arguments @(
        "-RuntimeVersion", $RuntimeVersion,
        "-LockedAttempt", $LockedAttempt,
        "-VideoAttempt", $VideoAttempt
    )

    $RequiredReports = @(Get-RequiredReportNames)
    $MissingReports = @(
        $RequiredReports |
            Where-Object {
                -not (Test-Path -LiteralPath (Join-Path $ProjectRoot "reports\$_") -PathType Leaf)
            }
    )
    if ($MissingReports.Count -gt 0) {
        throw "Final report publication is incomplete: $($MissingReports -join ', ')"
    }
    if (-not (Test-PublishedReports)) {
        throw "Published final artifacts failed schema or unit-test verification"
    }
    Write-StageEvent `
        -Stage "COMPLETE" -Status "COMPLETED" `
        -Hypothesis "Every required output is derived from frozen raw evidence." `
        -Result "Reports, claims audit, wording, metrics, videos, plots, tables, and passing test XML are published." `
        -NextAction "Use only the audited wording and values in reports/final_resume_wording_zh.md." `
        -Evidence @($RequiredReports | ForEach-Object { Join-Path $ProjectRoot "reports\$_" })
    Write-Output "COMPLETE: $ProjectRoot"
} catch {
    $Failure = $_.Exception.Message
    $Current = "BLOCKED"
    if (Test-Path -LiteralPath $StatePath -PathType Leaf) {
        try {
            $Current = [string](
                (Get-Content -LiteralPath $StatePath -Raw | ConvertFrom-Json).current_stage
            )
        } catch {
            $Current = "BLOCKED"
        }
    }
    Write-StageEvent `
        -Stage $Current -Status "BLOCKED" `
        -Hypothesis "The current gate must preserve failed evidence rather than silently retry or fabricate output." `
        -Result $Failure `
        -NextAction "Inspect the recorded evidence and launch a new immutable attempt only after diagnosis."
    throw
}
