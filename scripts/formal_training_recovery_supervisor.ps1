[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [int]$ObservedWrapperPid,
    [ValidateSet("B", "C")]
    [string]$Method = "B",
    [int]$RecoveryAttempt = 2,
    [ValidateSet(11, 29, 47)]
    [int]$StartSeed = 11,
    [ValidateSet(75, 100)]
    [int]$StartHeight = 75,
    [ValidateRange(5, 60)]
    [int]$PollSeconds = 20
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$MethodFolder = if ($Method -eq "B") { "ppo_without_com" } else { "ppo_with_com" }
$MethodRoot = Join-Path $ProjectRoot "runs\$MethodFolder"
$StatusPath = Join-Path $MethodRoot (
    "formal_v34_recovery_supervisor_attempt$('{0:D3}' -f $RecoveryAttempt).json"
)
$StdoutLog = Join-Path $MethodRoot (
    "formal_v34_training_recovery_attempt$('{0:D3}' -f $RecoveryAttempt).stdout.log"
)
$StderrLog = Join-Path $MethodRoot (
    "formal_v34_training_recovery_attempt$('{0:D3}' -f $RecoveryAttempt).stderr.log"
)
$HeartbeatPath = Join-Path $MethodRoot (
    "formal_v34_recovery_attempt$('{0:D3}' -f $RecoveryAttempt)_heartbeat.json"
)
$MonitorStdout = Join-Path $MethodRoot (
    "formal_v34_recovery_monitor_attempt$('{0:D3}' -f $RecoveryAttempt).stdout.log"
)
$MonitorStderr = Join-Path $MethodRoot (
    "formal_v34_recovery_monitor_attempt$('{0:D3}' -f $RecoveryAttempt).stderr.log"
)
$Seed50Run = Join-Path $MethodRoot (
    "training\method-$Method-v34_seed-$StartSeed`_stage-50mm_attempt001"
)
$Seed50Result = Join-Path $Seed50Run "training_result.json"
$Seed50Checkpoint = Join-Path $Seed50Run "checkpoints\final_agent.pt"
$Seed50Gate = Join-Path $MethodRoot (
    "development_gates\method-$Method-v34_seed-$StartSeed`_stage-50mm_attempt001"
)
$Seed50GateResult = Join-Path $Seed50Gate "result.json"
$Seed50GateDecision = Join-Path $Seed50Gate "gate_decision.json"

function Write-SupervisorStatus {
    param(
        [string]$Status,
        [string]$Message,
        [hashtable]$Additional = @{}
    )
    $Payload = [ordered]@{
        schema = "resume_validation.formal_recovery_supervisor.v1"
        updated_utc = (Get-Date).ToUniversalTime().ToString("o")
        supervisor_pid = $PID
        observed_wrapper_pid = $ObservedWrapperPid
        method = $Method
        recovery_attempt = $RecoveryAttempt
        start_seed = $StartSeed
        start_height_mm = $StartHeight
        status = $Status
        message = $Message
        locked_test_access = "forbidden"
    }
    foreach ($Key in $Additional.Keys) {
        $Payload[$Key] = $Additional[$Key]
    }
    $Directory = Split-Path -Parent $StatusPath
    New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    $Temporary = Join-Path $Directory (
        ".{0}.{1}.tmp" -f
        (Split-Path -Leaf $StatusPath),
        ([Guid]::NewGuid().ToString("N"))
    )
    $Payload | ConvertTo-Json -Depth 20 |
        Set-Content -LiteralPath $Temporary -Encoding UTF8
    Move-Item -LiteralPath $Temporary -Destination $StatusPath -Force
}

function Get-LiveEnvironmentProcess {
    param([string]$RunName = "")
    return @(
        Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
            Where-Object {
                $_.Name -eq "python.exe" -and
                $_.CommandLine -like "*envs\env_isaaclab\python.exe*" -and
                $_.CommandLine -like "*train_residual_ppo.py*" -and
                (
                    [string]::IsNullOrWhiteSpace($RunName) -or
                    $_.CommandLine -like "*$RunName*"
                )
            }
    )
}

function Test-CompletedStratumEvidence {
    param(
        [ValidateSet("B", "C")]
        [string]$EvidenceMethod,
        [int]$EvidenceSeed,
        [int]$EvidenceHeight,
        [System.IO.DirectoryInfo]$TrainingDirectory
    )
    try {
        $TrainingResultPath = Join-Path $TrainingDirectory.FullName "training_result.json"
        $ExpectedCheckpoint = Join-Path $TrainingDirectory.FullName "checkpoints\final_agent.pt"
        if (
            -not (Test-Path -LiteralPath $TrainingResultPath -PathType Leaf) -or
            -not (Test-Path -LiteralPath $ExpectedCheckpoint -PathType Leaf)
        ) {
            return $false
        }
        $TrainingResult = Get-Content -LiteralPath $TrainingResultPath -Raw |
            ConvertFrom-Json
        if (
            [string]$TrainingResult.status -ne "COMPLETED" -or
            [string]$TrainingResult.method -ne $EvidenceMethod -or
            [int]$TrainingResult.seed -ne $EvidenceSeed -or
            [int]$TrainingResult.height_mm -ne $EvidenceHeight -or
            [int]$TrainingResult.training_budget.local_timesteps_requested -ne 76800 -or
            [int]$TrainingResult.training_budget.local_timesteps_completed -ne 76800 -or
            [int]$TrainingResult.training_budget.local_transitions_requested -ne 4915200 -or
            [int]$TrainingResult.training_budget.local_transitions_completed -ne 4915200 -or
            [int]$TrainingResult.training_budget.parallel_environments -ne 64 -or
            @($TrainingResult.failures).Count -ne 0
        ) {
            return $false
        }
        $CheckpointHash = (
            Get-FileHash -LiteralPath $ExpectedCheckpoint -Algorithm SHA256
        ).Hash.ToLowerInvariant()
        if (
            $CheckpointHash -ne
            ([string]$TrainingResult.final_checkpoint.sha256).ToLowerInvariant()
        ) {
            return $false
        }

        $GateDirectory = Join-Path (
            Join-Path $MethodRoot "development_gates"
        ) $TrainingDirectory.Name
        $GateResultPath = Join-Path $GateDirectory "result.json"
        $GateDecisionPath = Join-Path $GateDirectory "gate_decision.json"
        if (
            -not (Test-Path -LiteralPath $GateResultPath -PathType Leaf) -or
            -not (Test-Path -LiteralPath $GateDecisionPath -PathType Leaf)
        ) {
            return $false
        }
        $GateResult = Get-Content -LiteralPath $GateResultPath -Raw |
            ConvertFrom-Json
        $GateDecision = Get-Content -LiteralPath $GateDecisionPath -Raw |
            ConvertFrom-Json
        $GateResultHash = (
            Get-FileHash -LiteralPath $GateResultPath -Algorithm SHA256
        ).Hash.ToLowerInvariant()
        if (
            -not [bool]$GateResult.passed_execution -or
            [string]$GateResult.controller -ne $EvidenceMethod -or
            [int]$GateResult.height_mm -ne $EvidenceHeight -or
            [int]$GateResult.aggregate.episode_count -ne 20 -or
            [string]$GateResult.provenance.checkpoint_sha256 -ne $CheckpointHash -or
            [string]$GateDecision.method -ne $EvidenceMethod -or
            [int]$GateDecision.seed -ne $EvidenceSeed -or
            [int]$GateDecision.height_mm -ne $EvidenceHeight -or
            [int]$GateDecision.actual.development_episode_count -ne 20 -or
            [string]$GateDecision.checkpoint_sha256 -ne $CheckpointHash -or
            ([string]$GateDecision.evaluation_sha256).ToLowerInvariant() -ne
                $GateResultHash -or
            -not [bool]$GateDecision.checks.checkpoint_hash_matches -or
            -not [bool]$GateDecision.checks.controller_matches -or
            -not [bool]$GateDecision.checks.episode_count_sufficient -or
            -not [bool]$GateDecision.checks.evaluation_completed -or
            -not [bool]$GateDecision.checks.height_matches
        ) {
            return $false
        }
        foreach ($ArtifactName in @("episodes", "status", "telemetry")) {
            $ArtifactPath = [string](
                $GateResult.artifacts.PSObject.Properties[$ArtifactName].Value
            )
            $HashProperty = "${ArtifactName}_sha256"
            $ExpectedHash = [string](
                $GateResult.artifacts.PSObject.Properties[$HashProperty].Value
            )
            if (
                -not (Test-Path -LiteralPath $ArtifactPath -PathType Leaf) -or
                (Get-FileHash -LiteralPath $ArtifactPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne
                    $ExpectedHash.ToLowerInvariant()
            ) {
                return $false
            }
        }
        return $true
    } catch {
        return $false
    }
}

$OwnsStatusPath = $false
try {
    if (Test-Path -LiteralPath $StatusPath -PathType Leaf) {
        $Existing = Get-Content -LiteralPath $StatusPath -Raw | ConvertFrom-Json
        if ($Existing.status -in @("WAITING", "RUNNING")) {
            throw "A recovery supervisor is already active or unresolved: $StatusPath"
        }
        throw "Recovery attempt evidence already exists; increment -RecoveryAttempt: $StatusPath"
    }
    foreach ($Path in @(
        $StdoutLog,
        $StderrLog,
        $HeartbeatPath,
        $MonitorStdout,
        $MonitorStderr
    )) {
        if (Test-Path -LiteralPath $Path) {
            throw "Recovery output already exists; increment -RecoveryAttempt: $Path"
        }
    }

    $OwnsStatusPath = $true
    Write-SupervisorStatus `
        -Status "WAITING" `
        -Message "Waiting for the observed wrapper to exit; no intervention is authorized while it is alive."
    while ($null -ne (Get-Process -Id $ObservedWrapperPid -ErrorAction SilentlyContinue)) {
        Start-Sleep -Seconds $PollSeconds
    }

    $WaitDeadline = (Get-Date).AddMinutes(5)
    do {
        $Live = @(Get-LiveEnvironmentProcess)
        if ($Live.Count -eq 0) {
            break
        }
        Start-Sleep -Seconds $PollSeconds
    } while ((Get-Date) -lt $WaitDeadline)
    if ($Live.Count -gt 0) {
        $Descriptions = ($Live | ForEach-Object {
            "pid=$($_.ProcessId) command=$($_.CommandLine)"
        }) -join " | "
        throw "Observed wrapper exited but Isaac training remains alive: $Descriptions"
    }

    if (-not (Test-Path -LiteralPath $Seed50Result -PathType Leaf)) {
        throw "Completed 50mm result is missing: $Seed50Result"
    }
    if (-not (Test-Path -LiteralPath $Seed50Checkpoint -PathType Leaf)) {
        throw "Completed 50mm checkpoint is missing: $Seed50Checkpoint"
    }
    $Training = Get-Content -LiteralPath $Seed50Result -Raw | ConvertFrom-Json
    if (
        $Training.status -ne "COMPLETED" -or
        [int]$Training.seed -ne $StartSeed -or
        [int]$Training.height_mm -ne 50 -or
        $Training.method -ne $Method
    ) {
        throw "50mm source stage is not a matching COMPLETED run: $Seed50Result"
    }
    $CheckpointHash = (
        Get-FileHash -LiteralPath $Seed50Checkpoint -Algorithm SHA256
    ).Hash.ToLowerInvariant()
    if ($CheckpointHash -ne [string]$Training.final_checkpoint.sha256) {
        throw "50mm source checkpoint hash mismatch: $Seed50Checkpoint"
    }
    if (
        -not (Test-Path -LiteralPath $Seed50GateResult -PathType Leaf) -or
        -not (Test-Path -LiteralPath $Seed50GateDecision -PathType Leaf)
    ) {
        throw "50mm development gate evidence is incomplete: $Seed50Gate"
    }
    $Gate = Get-Content -LiteralPath $Seed50GateResult -Raw | ConvertFrom-Json
    if (-not [bool]$Gate.passed_execution) {
        throw "50mm development evaluation did not pass execution: $Seed50GateResult"
    }

    $RunName = (
        "method-$Method-v34_seed-$StartSeed`_stage-${StartHeight}mm_" +
        "attempt$('{0:D3}' -f $RecoveryAttempt)"
    )
    $RecoveryRun = Join-Path $MethodRoot "training\$RunName"
    if (Test-Path -LiteralPath $RecoveryRun) {
        throw "Recovery run directory already exists: $RecoveryRun"
    }
    $WrapperName = if ($Method -eq "B") {
        "05_train_B.ps1"
    } else {
        "06_train_C.ps1"
    }
    $Wrapper = Join-Path $PSScriptRoot $WrapperName
    $Arguments = @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", $Wrapper,
        "-Iterations", "1200",
        "-NumEnvs", "64",
        "-Rollouts", "64",
        "-Attempt", [string]$RecoveryAttempt,
        "-RuntimeVersion", "v34",
        "-StartSeed", [string]$StartSeed,
        "-StartHeight", [string]$StartHeight,
        "-InitialResumeCheckpoint", $Seed50Checkpoint,
        "-ContinueAfterFailedGate"
    )
    $RecoveryProcess = Start-Process `
        -FilePath "powershell.exe" `
        -ArgumentList $Arguments `
        -RedirectStandardOutput $StdoutLog `
        -RedirectStandardError $StderrLog `
        -WindowStyle Hidden `
        -PassThru

    $MonitorScript = Join-Path $PSScriptRoot "formal_training_monitor.ps1"
    $MonitorArguments = @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", $MonitorScript,
        "-WrapperPid", [string]$RecoveryProcess.Id,
        "-Method", $Method,
        "-StdoutLog", $StdoutLog,
        "-StderrLog", $StderrLog,
        "-HeartbeatPath", $HeartbeatPath,
        "-PollSeconds", "20",
        "-SilenceMinutes", "20"
    )
    $MonitorProcess = Start-Process `
        -FilePath "powershell.exe" `
        -ArgumentList $MonitorArguments `
        -RedirectStandardOutput $MonitorStdout `
        -RedirectStandardError $MonitorStderr `
        -WindowStyle Hidden `
        -PassThru

    Write-SupervisorStatus `
        -Status "RUNNING" `
        -Message "Launched a new immutable recovery wrapper and project-scoped monitor." `
        -Additional @{
            recovery_wrapper_pid = $RecoveryProcess.Id
            monitor_pid = $MonitorProcess.Id
            source_checkpoint = $Seed50Checkpoint
            source_checkpoint_sha256 = $CheckpointHash
            stdout_log = $StdoutLog
            stderr_log = $StderrLog
            heartbeat = $HeartbeatPath
        }

    $RecoveryProcess.WaitForExit()
    $RecoveryProcess.Refresh()
    $ExitCode = $RecoveryProcess.ExitCode
    $Completed = @()
    foreach ($Seed in @(11, 29, 47)) {
        foreach ($Height in @(50, 75, 100)) {
            $Candidates = @(
                Get-ChildItem -LiteralPath (Join-Path $MethodRoot "training") `
                    -Directory `
                    -Filter "method-$Method-v34_seed-$Seed`_stage-${Height}mm_attempt*" `
                    -ErrorAction SilentlyContinue
            )
            $Verified = @(
                $Candidates |
                    Where-Object {
                        Test-CompletedStratumEvidence `
                            -EvidenceMethod $Method `
                            -EvidenceSeed $Seed `
                            -EvidenceHeight $Height `
                            -TrainingDirectory $_
                    }
            )
            if ($Verified.Count -gt 0) {
                $Completed += "$Method/$Seed/${Height}mm"
            }
        }
    }
    if ($null -ne $ExitCode -and [int]$ExitCode -ne 0) {
        throw "Recovery wrapper exited with code $ExitCode"
    }
    if ($Completed.Count -ne 9) {
        throw (
            "Recovery wrapper returned without complete, hash-verified " +
            "training and development-gate evidence for all 9 Method-$Method strata"
        )
    }
    $CompletionBasis = if ($null -eq $ExitCode) {
        "The wrapper exit code was unavailable; all nine training results, checkpoints, and development-gate artifact hash chains independently verified."
    } else {
        "The wrapper returned exit code 0 and all nine training results, checkpoints, and development-gate artifact hash chains independently verified."
    }
    Write-SupervisorStatus `
        -Status "COMPLETED" `
        -Message $CompletionBasis `
        -Additional @{
            recovery_wrapper_pid = $RecoveryProcess.Id
            monitor_pid = $MonitorProcess.Id
            recovery_exit_code = $ExitCode
            completed_strata = $Completed
            stdout_log = $StdoutLog
            stderr_log = $StderrLog
            heartbeat = $HeartbeatPath
        }
} catch {
    if ($OwnsStatusPath) {
        Write-SupervisorStatus `
            -Status "FAILED" `
            -Message $_.Exception.Message `
            -Additional @{
                failure_type = $_.Exception.GetType().FullName
                traceback = $_.ScriptStackTrace
            }
    } else {
        Write-Error $_.Exception.Message
    }
    exit 1
}
