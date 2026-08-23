param(
    [Parameter(Mandatory = $true)]
    [int]$WrapperPid,
    [Parameter(Mandatory = $true)]
    [ValidateSet("B", "C")]
    [string]$Method,
    [Parameter(Mandatory = $true)]
    [string]$StdoutLog,
    [Parameter(Mandatory = $true)]
    [string]$StderrLog,
    [Parameter(Mandatory = $true)]
    [string]$HeartbeatPath,
    [ValidateRange(10, 60)]
    [int]$PollSeconds = 20,
    [ValidateRange(5, 120)]
    [int]$SilenceMinutes = 20
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ResolvedStdout = [IO.Path]::GetFullPath($StdoutLog)
$ResolvedStderr = [IO.Path]::GetFullPath($StderrLog)
$ResolvedHeartbeat = [IO.Path]::GetFullPath($HeartbeatPath)
$DiagnosticRoot = Join-Path $ProjectRoot "runs\diagnostics\training_monitor"
New-Item -ItemType Directory -Path $DiagnosticRoot -Force | Out-Null
New-Item -ItemType Directory -Path (Split-Path -Parent $ResolvedHeartbeat) -Force | Out-Null
$PreviousStep = $null
$PreviousStepTime = $null
$SilenceDiagnosticWritten = $false

function Write-AtomicJson {
    param([string]$Path, [object]$Payload)
    $Temporary = "$Path.tmp"
    $Payload | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $Temporary -Encoding UTF8
    Move-Item -LiteralPath $Temporary -Destination $Path -Force
}

while ($true) {
    $Now = Get-Date
    $Wrapper = Get-Process -Id $WrapperPid -ErrorAction SilentlyContinue
    $Processes = @(
        Get-CimInstance Win32_Process |
            Where-Object {
                $_.CommandLine -like "*resume_validation_fsm_residual_ppo*" -and
                (
                    $_.CommandLine -like "*train_residual_ppo.py*" -or
                    $_.CommandLine -like "*evaluate_controller.py*" -or
                    $_.ProcessId -eq $WrapperPid
                )
            }
    )
    $EnvironmentPython = @(
        $Processes |
            Where-Object {
                $_.Name -eq "python.exe" -and
                $_.ExecutablePath -like "*envs\env_isaaclab\python.exe"
            }
    )
    $Tail = if (Test-Path -LiteralPath $ResolvedStdout) {
        Get-Content -LiteralPath $ResolvedStdout -Tail 300 -ErrorAction SilentlyContinue
    } else {
        @()
    }
    $TailText = $Tail -join "`n"
    $ProgressMatches = [regex]::Matches($TailText, "(\d+)/(\d+)")
    $CurrentStep = $null
    $TotalStep = $null
    if ($ProgressMatches.Count -gt 0) {
        $LastProgress = $ProgressMatches[$ProgressMatches.Count - 1]
        $CurrentStep = [int64]$LastProgress.Groups[1].Value
        $TotalStep = [int64]$LastProgress.Groups[2].Value
    }
    $ControlStepsPerSecond = $null
    if (
        $null -ne $CurrentStep -and
        $null -ne $PreviousStep -and
        $null -ne $PreviousStepTime -and
        ($Now - $PreviousStepTime).TotalSeconds -gt 0
    ) {
        $ControlStepsPerSecond = (
            $CurrentStep - $PreviousStep
        ) / ($Now - $PreviousStepTime).TotalSeconds
    }
    if ($null -ne $CurrentStep) {
        $PreviousStep = $CurrentStep
        $PreviousStepTime = $Now
    }
    $ActiveCommand = @(
        $EnvironmentPython |
            Select-Object -First 1 -ExpandProperty CommandLine
    )
    $CommandText = if ($ActiveCommand.Count -gt 0) { [string]$ActiveCommand[0] } else { "" }
    $SeedMatch = [regex]::Match($CommandText, "--seed\s+(\d+)")
    $HeightMatch = [regex]::Match($CommandText, "--height_mm\s+(\d+)")
    $RunMatch = [regex]::Match($CommandText, "--run_name\s+([^\s""]+)")
    $CurrentRunName = if ($RunMatch.Success) { $RunMatch.Groups[1].Value } else { "" }

    $LatestCheckpoint = Get-ChildItem `
        -Path (Join-Path $ProjectRoot "runs") `
        -Recurse `
        -File `
        -Filter "*.pt" `
        -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -like "*method-$Method-v34*" } |
        Sort-Object LastWriteTimeUtc -Descending |
        Select-Object -First 1
    $LatestArtifact = Get-ChildItem `
        -Path (Join-Path $ProjectRoot "runs") `
        -Recurse `
        -File `
        -ErrorAction SilentlyContinue |
        Where-Object {
            $_.FullName -like "*ppo_*com*" -or
            $_.FullName -like "*method-$Method-v34*"
        } |
        Sort-Object LastWriteTimeUtc -Descending |
        Select-Object -First 1
    $LogWrite = if (Test-Path -LiteralPath $ResolvedStdout) {
        (Get-Item -LiteralPath $ResolvedStdout).LastWriteTimeUtc
    } else {
        [datetime]::MinValue
    }
    $LatestWrite = $LogWrite
    if ($null -ne $LatestArtifact -and $LatestArtifact.LastWriteTimeUtc -gt $LatestWrite) {
        $LatestWrite = $LatestArtifact.LastWriteTimeUtc
    }
    $SilenceSeconds = if ($LatestWrite -eq [datetime]::MinValue) {
        $null
    } else {
        ([datetime]::UtcNow - $LatestWrite).TotalSeconds
    }
    $HangSuspected = (
        $null -ne $Wrapper -and
        $null -ne $SilenceSeconds -and
        $SilenceSeconds -ge $SilenceMinutes * 60
    )
    $Gpu = & nvidia-smi `
        --query-gpu=memory.used,memory.total,utilization.gpu `
        --format=csv,noheader,nounits 2>$null
    $GpuFields = if ($Gpu) { ([string]$Gpu).Split(",") | ForEach-Object { $_.Trim() } } else { @() }
    $ErrorText = $TailText
    if (Test-Path -LiteralPath $ResolvedStderr) {
        $ErrorText += "`n" + (
            Get-Content -LiteralPath $ResolvedStderr -Tail 300 -ErrorAction SilentlyContinue
        ) -join "`n"
    }
    $Heartbeat = [ordered]@{
        schema = "resume_validation.training_heartbeat.v1"
        updated_utc = [datetime]::UtcNow.ToString("o")
        wrapper_pid = $WrapperPid
        wrapper_alive = $null -ne $Wrapper
        child_pids = @($Processes | Where-Object { $_.ProcessId -ne $WrapperPid } | Select-Object -ExpandProperty ProcessId)
        environment_python_pids = @($EnvironmentPython | Select-Object -ExpandProperty ProcessId)
        stage = if ($CommandText -like "*evaluate_controller.py*") { "development_evaluation" } elseif ($CommandText -like "*train_residual_ppo.py*") { "training" } else { "transition_or_finished" }
        method = $Method
        seed = if ($SeedMatch.Success) { [int]$SeedMatch.Groups[1].Value } else { $null }
        height_mm = if ($HeightMatch.Success) { [int]$HeightMatch.Groups[1].Value } else { $null }
        run_name = $CurrentRunName
        local_control_timestep = $CurrentStep
        total_local_control_timesteps = $TotalStep
        control_steps_per_second = $ControlStepsPerSecond
        elapsed_wall_time_s = if ($null -ne $Wrapper) { ($Now - $Wrapper.StartTime).TotalSeconds } else { $null }
        gpu_memory_used_mib = if ($GpuFields.Count -ge 1) { [int]$GpuFields[0] } else { $null }
        gpu_memory_total_mib = if ($GpuFields.Count -ge 2) { [int]$GpuFields[1] } else { $null }
        gpu_utilization_percent = if ($GpuFields.Count -ge 3) { [int]$GpuFields[2] } else { $null }
        latest_train_return = $null
        latest_success_rate = $null
        latest_validation_success = $null
        nan_inf_mentions_in_tail = ([regex]::Matches($ErrorText, "(?i)\b(?:nan|inf)\b")).Count
        oom_mentions_in_tail = ([regex]::Matches($ErrorText, "(?i)out of memory|CUDA OOM")).Count
        traceback_mentions_in_tail = ([regex]::Matches($ErrorText, "Traceback \(most recent call last\)")).Count
        checkpoint = if ($null -ne $LatestCheckpoint) { $LatestCheckpoint.FullName } else { $null }
        checkpoint_last_write_utc = if ($null -ne $LatestCheckpoint) { $LatestCheckpoint.LastWriteTimeUtc.ToString("o") } else { $null }
        last_log_or_artifact_time_utc = if ($LatestWrite -ne [datetime]::MinValue) { $LatestWrite.ToString("o") } else { $null }
        silence_seconds = $SilenceSeconds
        hang_suspected = $HangSuspected
        stdout_log = $ResolvedStdout
        stderr_log = $ResolvedStderr
        intervention_policy = "diagnose-only; never terminate unrelated processes; recovery is launched with a new preserved attempt"
    }
    Write-AtomicJson -Path $ResolvedHeartbeat -Payload $Heartbeat

    if ($HangSuspected -and -not $SilenceDiagnosticWritten) {
        $DiagnosticPath = Join-Path $DiagnosticRoot (
            "silence_method-$Method`_wrapper-$WrapperPid`_" +
            [datetime]::UtcNow.ToString("yyyyMMdd_HHmmss") + ".json"
        )
        $Diagnostic = [ordered]@{
            schema = "resume_validation.training_silence_diagnostic.v1"
            heartbeat = $Heartbeat
            process_commands = @($Processes | Select-Object ProcessId, ParentProcessId, Name, ExecutablePath, CommandLine)
            stdout_tail = $TailText
            stderr_tail = if (Test-Path -LiteralPath $ResolvedStderr) { (Get-Content -LiteralPath $ResolvedStderr -Tail 500) -join "`n" } else { "" }
            action = "preserved diagnostic; no automatic kill because stage transitions and long Isaac shutdowns must be distinguished from a hang"
        }
        Write-AtomicJson -Path $DiagnosticPath -Payload $Diagnostic
        $SilenceDiagnosticWritten = $true
    }
    if (-not $HangSuspected) {
        $SilenceDiagnosticWritten = $false
    }
    if ($null -eq $Wrapper) {
        break
    }
    Start-Sleep -Seconds $PollSeconds
}
