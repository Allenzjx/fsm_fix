[CmdletBinding()]
param(
    [ValidateRange(1, 999)]
    [int]$Attempt = 1,
    [ValidateRange(10, 60)]
    [int]$PollSeconds = 30,
    [string]$RuntimeVersion = "v34",
    [int]$ValidationAttempt = 1,
    [int]$VideoSmokeAttempt = 1,
    [int]$LockedAttempt = 1,
    [int]$VideoAttempt = 1
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$OrchestrationRoot = Join-Path $ProjectRoot "runs\orchestration"
$StatusPath = Join-Path $OrchestrationRoot (
    "full_pipeline_supervisor_attempt$('{0:D3}' -f $Attempt).json"
)
$RecoveryStatusPath = Join-Path $ProjectRoot (
    "runs\ppo_without_com\formal_v34_recovery_supervisor_attempt002.json"
)
$Runner = Join-Path $PSScriptRoot "run_until_success.ps1"

function Write-SupervisorStatus {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Status,
        [Parameter(Mandatory = $true)]
        [string]$Message,
        [hashtable]$Additional = @{}
    )
    $Payload = [ordered]@{
        schema = "resume_validation.full_pipeline_supervisor.v1"
        updated_utc = (Get-Date).ToUniversalTime().ToString("o")
        supervisor_pid = $PID
        attempt = $Attempt
        status = $Status
        message = $Message
        runtime_version = $RuntimeVersion
        locked_test_access = (
            "delegated only to run_until_success after verified method freeze"
        )
    }
    foreach ($Key in $Additional.Keys) {
        $Payload[$Key] = $Additional[$Key]
    }
    New-Item -ItemType Directory -Path $OrchestrationRoot -Force | Out-Null
    $Temporary = Join-Path $OrchestrationRoot (
        ".{0}.{1}.tmp" -f
        (Split-Path -Leaf $StatusPath),
        ([Guid]::NewGuid().ToString("N"))
    )
    $Payload | ConvertTo-Json -Depth 20 |
        Set-Content -LiteralPath $Temporary -Encoding UTF8
    Move-Item -LiteralPath $Temporary -Destination $StatusPath -Force
}

function Get-LiveFormalTraining {
    return @(
        Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
            Where-Object {
                $_.Name -eq "python.exe" -and
                $_.CommandLine -like "*envs\env_isaaclab\python.exe*" -and
                $_.CommandLine -like "*train_residual_ppo.py*"
            } |
            Select-Object ProcessId, ParentProcessId, CommandLine
    )
}

function Test-CompleteMethodBRecoveryEvidence {
    $MethodRoot = Join-Path $ProjectRoot "runs\ppo_without_com"
    $TrainingRoot = Join-Path $MethodRoot "training"
    if (-not (Test-Path -LiteralPath $TrainingRoot -PathType Container)) {
        return $false
    }
    foreach ($EvidenceSeed in @(11, 29, 47)) {
        foreach ($EvidenceHeight in @(50, 75, 100)) {
            $Verified = $false
            $Candidates = @(
                Get-ChildItem -LiteralPath $TrainingRoot `
                    -Directory `
                    -Filter "method-B-v34_seed-$EvidenceSeed`_stage-${EvidenceHeight}mm_attempt*" `
                    -ErrorAction SilentlyContinue
            )
            foreach ($TrainingDirectory in $Candidates) {
                try {
                    $TrainingResultPath = Join-Path $TrainingDirectory.FullName "training_result.json"
                    $ExpectedCheckpoint = Join-Path $TrainingDirectory.FullName "checkpoints\final_agent.pt"
                    if (
                        -not (Test-Path -LiteralPath $TrainingResultPath -PathType Leaf) -or
                        -not (Test-Path -LiteralPath $ExpectedCheckpoint -PathType Leaf)
                    ) {
                        continue
                    }
                    $TrainingResult = Get-Content -LiteralPath $TrainingResultPath -Raw |
                        ConvertFrom-Json
                    if (
                        [string]$TrainingResult.status -ne "COMPLETED" -or
                        [string]$TrainingResult.method -ne "B" -or
                        [int]$TrainingResult.seed -ne $EvidenceSeed -or
                        [int]$TrainingResult.height_mm -ne $EvidenceHeight -or
                        [int]$TrainingResult.training_budget.local_timesteps_requested -ne 76800 -or
                        [int]$TrainingResult.training_budget.local_timesteps_completed -ne 76800 -or
                        [int]$TrainingResult.training_budget.local_transitions_requested -ne 4915200 -or
                        [int]$TrainingResult.training_budget.local_transitions_completed -ne 4915200 -or
                        [int]$TrainingResult.training_budget.parallel_environments -ne 64 -or
                        @($TrainingResult.failures).Count -ne 0
                    ) {
                        continue
                    }
                    $CheckpointHash = (
                        Get-FileHash -LiteralPath $ExpectedCheckpoint -Algorithm SHA256
                    ).Hash.ToLowerInvariant()
                    if (
                        $CheckpointHash -ne
                        ([string]$TrainingResult.final_checkpoint.sha256).ToLowerInvariant()
                    ) {
                        continue
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
                        continue
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
                        [string]$GateResult.controller -ne "B" -or
                        [int]$GateResult.height_mm -ne $EvidenceHeight -or
                        [int]$GateResult.aggregate.episode_count -ne 20 -or
                        [string]$GateResult.provenance.checkpoint_sha256 -ne $CheckpointHash -or
                        [string]$GateDecision.method -ne "B" -or
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
                        continue
                    }
                    $ArtifactsVerified = $true
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
                            $ArtifactsVerified = $false
                            break
                        }
                    }
                    if ($ArtifactsVerified) {
                        $Verified = $true
                        break
                    }
                } catch {
                    continue
                }
            }
            if (-not $Verified) {
                return $false
            }
        }
    }
    return $true
}

$OwnsStatus = $false
try {
    if (Test-Path -LiteralPath $StatusPath) {
        throw (
            "Supervisor attempt evidence already exists; increment -Attempt: " +
            $StatusPath
        )
    }
    $OwnsStatus = $true

    # The already-running one-shot B recovery supervisor owns the transition
    # from the historical attempt001 offset failure to corrected attempt002.
    # Waiting here closes the otherwise brief no-live-process race window.
    if (Test-Path -LiteralPath $RecoveryStatusPath -PathType Leaf) {
        while ($true) {
            $Recovery = Get-Content -LiteralPath $RecoveryStatusPath -Raw |
                ConvertFrom-Json
            $RecoveryStatus = [string]$Recovery.status
            if ($RecoveryStatus -eq "COMPLETED") {
                break
            }
            if ($RecoveryStatus -eq "FAILED") {
                if (Test-CompleteMethodBRecoveryEvidence) {
                    Write-SupervisorStatus `
                        -Status "METHOD_B_RECOVERED_FROM_EVIDENCE" `
                        -Message (
                            "The historical recovery supervisor reported failure because its " +
                            "wrapper exit code was unavailable; all 9 training/checkpoint and " +
                            "development-gate artifact hash chains independently verified."
                        ) `
                        -Additional @{
                            historical_recovery_status = $RecoveryStatus
                            historical_recovery_message = [string]$Recovery.message
                            verified_method_b_strata = 9
                        }
                    break
                }
                throw (
                    "Method-B recovery supervisor failed and complete evidence " +
                    "could not be independently verified: " +
                    [string]$Recovery.message
                )
            }
            if ($RecoveryStatus -notin @("WAITING", "RUNNING")) {
                throw "Unexpected Method-B recovery status: $RecoveryStatus"
            }
            $RecoveryPid = [int]$Recovery.supervisor_pid
            if ($null -eq (
                Get-Process -Id $RecoveryPid -ErrorAction SilentlyContinue
            )) {
                throw (
                    "Method-B recovery status is unresolved but its supervisor " +
                    "process is absent: pid=$RecoveryPid"
                )
            }
            $Live = @(Get-LiveFormalTraining)
            Write-SupervisorStatus `
                -Status "WAITING_FOR_METHOD_B_RECOVERY" `
                -Message "The existing recovery supervisor retains exclusive ownership of Method-B training." `
                -Additional @{
                    recovery_status = $RecoveryStatus
                    recovery_supervisor_pid = $RecoveryPid
                    live_training_pids = @($Live.ProcessId)
                }
            Start-Sleep -Seconds $PollSeconds
        }
    }

    $RunnerInvocation = 0
    while ($true) {
        $RunnerInvocation += 1
        $StdoutLog = Join-Path $OrchestrationRoot (
            "full_pipeline_attempt$('{0:D3}' -f $Attempt)" +
            "_runner$('{0:D3}' -f $RunnerInvocation).stdout.log"
        )
        $StderrLog = Join-Path $OrchestrationRoot (
            "full_pipeline_attempt$('{0:D3}' -f $Attempt)" +
            "_runner$('{0:D3}' -f $RunnerInvocation).stderr.log"
        )
        if (
            (Test-Path -LiteralPath $StdoutLog) -or
            (Test-Path -LiteralPath $StderrLog)
        ) {
            throw "Runner log collision: $StdoutLog or $StderrLog"
        }
        $Arguments = @(
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-File", $Runner,
            "-RuntimeVersion", $RuntimeVersion,
            "-ValidationAttempt", [string]$ValidationAttempt,
            "-VideoSmokeAttempt", [string]$VideoSmokeAttempt,
            "-LockedAttempt", [string]$LockedAttempt,
            "-VideoAttempt", [string]$VideoAttempt
        )
        $RunnerProcess = Start-Process `
            -FilePath "powershell.exe" `
            -ArgumentList $Arguments `
            -RedirectStandardOutput $StdoutLog `
            -RedirectStandardError $StderrLog `
            -WindowStyle Hidden `
            -PassThru
        while (-not $RunnerProcess.HasExited) {
            $RunnerProcess.Refresh()
            $Live = @(Get-LiveFormalTraining)
            Write-SupervisorStatus `
                -Status "RUNNING_PIPELINE" `
                -Message "The recoverable state machine is running; no second invocation is allowed." `
                -Additional @{
                    runner_invocation = $RunnerInvocation
                    runner_pid = $RunnerProcess.Id
                    stdout_log = $StdoutLog
                    stderr_log = $StderrLog
                    live_training_pids = @($Live.ProcessId)
                }
            Start-Sleep -Seconds $PollSeconds
        }
        $RunnerProcess.WaitForExit()
        $RunnerProcess.Refresh()
        $ExitCode = $RunnerProcess.ExitCode
        if ($null -eq $ExitCode) {
            $LiveAfterRunner = @(Get-LiveFormalTraining)
            $FinalAuditAfterRunner = Join-Path $ProjectRoot "reports\final_audit.json"
            if ($LiveAfterRunner.Count -gt 0) {
                $ExitCode = 3
            } elseif (Test-Path -LiteralPath $FinalAuditAfterRunner -PathType Leaf) {
                $AuditAfterRunner = Get-Content -LiteralPath $FinalAuditAfterRunner -Raw |
                    ConvertFrom-Json
                if (
                    [string]$AuditAfterRunner.status -in
                    @("PASS", "PASS_WITH_DISCLOSURES")
                ) {
                    $ExitCode = 0
                }
            }
            if ($null -eq $ExitCode) {
                throw (
                    "Recoverable state-machine exit code was unavailable and " +
                    "neither live formal training nor a passing final audit " +
                    "could independently establish its terminal state; inspect " +
                    "$StdoutLog and $StderrLog"
                )
            }
        }
        if ($ExitCode -eq 3) {
            Write-SupervisorStatus `
                -Status "WAITING_FOR_EXISTING_TRAINING" `
                -Message "The state machine found a live formal process and exited without launching a duplicate." `
                -Additional @{
                    runner_invocation = $RunnerInvocation
                    runner_exit_code = $ExitCode
                    stdout_log = $StdoutLog
                    stderr_log = $StderrLog
                    live_training_pids = @(
                        @(Get-LiveFormalTraining).ProcessId
                    )
                }
            Start-Sleep -Seconds $PollSeconds
            continue
        }
        if ($ExitCode -ne 0) {
            throw (
                "Recoverable state machine exited with code $ExitCode; " +
                "inspect $StdoutLog and $StderrLog"
            )
        }

        $FinalAuditPath = Join-Path $ProjectRoot "reports\final_audit.json"
        if (-not (Test-Path -LiteralPath $FinalAuditPath -PathType Leaf)) {
            throw "State machine returned success without final audit: $FinalAuditPath"
        }
        $FinalAudit = Get-Content -LiteralPath $FinalAuditPath -Raw |
            ConvertFrom-Json
        if ([string]$FinalAudit.status -notin @("PASS", "PASS_WITH_DISCLOSURES")) {
            throw "Final audit is not publishable: $($FinalAudit.status)"
        }
        Write-SupervisorStatus `
            -Status "COMPLETED" `
            -Message "The full frozen experiment, locked campaign, videos, reports, and final audit completed." `
            -Additional @{
                runner_invocation = $RunnerInvocation
                runner_exit_code = $ExitCode
                stdout_log = $StdoutLog
                stderr_log = $StderrLog
                final_audit = $FinalAuditPath
                final_audit_status = [string]$FinalAudit.status
            }
        break
    }
} catch {
    if ($OwnsStatus) {
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
