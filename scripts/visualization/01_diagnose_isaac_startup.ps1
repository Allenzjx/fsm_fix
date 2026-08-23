[CmdletBinding()]
param(
    [string]$ReportRoot = '',
    [switch]$SkipVisibleSmoke,
    [switch]$SkipOffscreenSmoke
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$IsaacLabRoot = 'C:\robotics_sim\IsaacLab'
$IsaacLabBat = 'C:\robotics_sim\IsaacLab\isaaclab.bat'
$CondaCandidates = @(
    'C:\Users\kskzz\miniconda3\Scripts\conda.exe',
    'C:\Users\kskzz\miniconda3\condabin\conda.bat'
)
$CondaExe = $CondaCandidates | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
if (-not $CondaExe) {
    $found = Get-Command conda.exe -ErrorAction SilentlyContinue
    if (-not $found) { $found = Get-Command conda -ErrorAction SilentlyContinue }
    if ($found) { $CondaExe = $found.Source }
}
if (-not $CondaExe) { throw 'Unable to locate Conda using the required discovery order.' }
if (-not (Test-Path -LiteralPath $IsaacLabBat -PathType Leaf)) { throw "Missing Isaac Lab launcher: $IsaacLabBat" }

if (-not $ReportRoot) {
    $ReportRoot = Join-Path $ProjectRoot ('reports\visualization_capture_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
}
$ReportRoot = [IO.Path]::GetFullPath($ReportRoot)
$DiagRoot = Join-Path $ReportRoot 'crash_diagnostics'
@(
    $ReportRoot,
    $DiagRoot,
    (Join-Path $DiagRoot 'kit_logs'),
    (Join-Path $DiagRoot 'windows_events'),
    (Join-Path $DiagRoot 'stdout'),
    (Join-Path $DiagRoot 'stderr'),
    (Join-Path $DiagRoot 'process_snapshots')
) | ForEach-Object { New-Item -ItemType Directory -Path $_ -Force | Out-Null }

function Get-ProjectWorkloads {
    $projectPattern = [regex]::Escape($ProjectRoot)
    $workloadPattern = 'train_residual_ppo\.py|evaluate_controller\.py|run_until_success\.ps1|06_train_C\.ps1|full_pipeline_supervisor\.ps1|pipeline_keep_awake\.ps1|isaac_startup_smoke\.py'
    @(Get-CimInstance Win32_Process | Where-Object {
        $_.ProcessId -ne $PID -and $_.CommandLine -and
        $_.CommandLine -match $projectPattern -and $_.CommandLine -match $workloadPattern
    } | Select-Object ProcessId,ParentProcessId,Name,CreationDate,CommandLine)
}

function Save-ProcessSnapshot {
    param([Parameter(Mandatory)][string]$Name)
    $all = Get-CimInstance Win32_Process | Where-Object {
        $_.Name -match 'python|kit|isaac|conda|powershell' -or
        ($_.CommandLine -and $_.CommandLine -match [regex]::Escape($ProjectRoot))
    } | Select-Object ProcessId,ParentProcessId,Name,CreationDate,CommandLine
    $all | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $DiagRoot "process_snapshots\$Name.json") -Encoding utf8
}

$blockers = @(Get-ProjectWorkloads)
Save-ProcessSnapshot -Name 'before_diagnosis'
if ($blockers.Count -gt 0) {
    $blockers | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $DiagRoot 'process_snapshots\blocking_workloads.json') -Encoding utf8
    throw "Startup diagnosis refused: active project workload PID(s): $(($blockers.ProcessId) -join ', ')"
}

$eventPath = Join-Path $DiagRoot 'windows_events\application_20260731_2135_2150.json'
$eventSummaryPath = Join-Path $DiagRoot 'windows_events\matching_summary.txt'
try {
    $events = @(Get-WinEvent -FilterHashtable @{
        LogName = 'Application'
        StartTime = [datetime]'2026-07-31T21:35:00'
        EndTime = [datetime]'2026-07-31T21:50:00'
    } | Select-Object @{n='TimeCreated';e={$_.TimeCreated.ToString('o')}},Id,LevelDisplayName,ProviderName,Message)
    $events | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $eventPath -Encoding utf8
    $matches = @($events | Where-Object {
        $_.ProviderName -match 'Application Error|Windows Error Reporting|NVIDIA|Vulkan|carb' -or
        $_.Message -match 'python\.exe|kit\.exe|isaac-sim|nvwgf2umx|NVIDIA|Vulkan|carb'
    })
    $matches | Format-List | Out-String | Set-Content -LiteralPath $eventSummaryPath -Encoding utf8
} catch {
    "Get-WinEvent failed: $($_.Exception.Message)" | Set-Content -LiteralPath $eventSummaryPath -Encoding utf8
    '[]' | Set-Content -LiteralPath $eventPath -Encoding utf8
}

$SmokeScript = Join-Path $ProjectRoot 'tools\visualization\isaac_startup_smoke.py'
$attempts = [System.Collections.Generic.List[object]]::new()
$historicalRoot = Join-Path $ProjectRoot 'reports\chatgpt_handoff_20260731_171825\gui_runs'
Get-ChildItem -LiteralPath $historicalRoot -Directory -Filter 'fsm_50mm_development-h050-0000_*' -ErrorAction SilentlyContinue | Sort-Object Name | ForEach-Object {
    $attempts.Add([pscustomobject]@{
        attempt_id = $_.Name
        mode = 'historical-visible-controller'
        command = 'historical wrapper did not persist the exact command'
        working_directory = $IsaacLabRoot
        parent_pid = ''
        child_pid = ''
        started_at = $_.CreationTime.ToString('o')
        ended_at = $_.LastWriteTime.ToString('o')
        exit_code = 'UNKNOWN_NOT_RECORDED'
        duration_s = ''
        stdout_path = (Join-Path $_.FullName 'viewer.log')
        stderr_path = ''
        kit_log_path = ''
        result_path = (Join-Path $_.FullName 'result.json')
        status = if (Test-Path -LiteralPath (Join-Path $_.FullName 'result.json')) { 'HAS_RESULT' } else { 'STARTUP_EXIT_BEFORE_EVALUATION' }
    })
}

function Invoke-IsaacSmoke {
    param(
        [Parameter(Mandatory)][ValidateSet('visible','offscreen')][string]$Mode
    )
    $isHeadless = $Mode -eq 'offscreen'
    $attemptId = "${Mode}_smoke_" + (Get-Date -Format 'yyyyMMdd_HHmmss_fff')
    $output = Join-Path $DiagRoot $attemptId
    $stdout = Join-Path $DiagRoot "stdout\$attemptId.log"
    $stderr = Join-Path $DiagRoot "stderr\$attemptId.log"
    $kitBefore = @(Get-ChildItem -LiteralPath 'C:\Users\kskzz\miniconda3\envs\env_isaaclab\Lib\site-packages\isaacsim\kit\logs\Kit\Isaac-Sim\5.1' -File -Filter 'kit_*.log' | Sort-Object LastWriteTime)
    $arguments = @(
        'run','--no-capture-output','-n','env_isaaclab',
        $IsaacLabBat,'-p',$SmokeScript,
        '--output-dir',$output,
        '--frames','120'
    )
    if ($isHeadless) { $arguments += @('--headless','--enable_cameras','--capture-images') }
    $command = "`"$CondaExe`" " + (($arguments | ForEach-Object { if ($_ -match '\s') { "`"$_`"" } else { $_ } }) -join ' ')
    $start = Get-Date
    $proc = $null
    $exitCode = $null
    try {
        $startParams = @{
            FilePath = $CondaExe
            ArgumentList = $arguments
            WorkingDirectory = $IsaacLabRoot
            RedirectStandardOutput = $stdout
            RedirectStandardError = $stderr
            PassThru = $true
            Wait = $true
        }
        if ($isHeadless) { $startParams.WindowStyle = 'Hidden' }
        $proc = Start-Process @startParams
        $exitCode = $proc.ExitCode
    } catch {
        $_ | Out-String | Add-Content -LiteralPath $stderr -Encoding utf8
        $exitCode = -1
    }
    $end = Get-Date
    $kitAfter = @(Get-ChildItem -LiteralPath 'C:\Users\kskzz\miniconda3\envs\env_isaaclab\Lib\site-packages\isaacsim\kit\logs\Kit\Isaac-Sim\5.1' -File -Filter 'kit_*.log' | Sort-Object LastWriteTime)
    $latestKit = if ($kitAfter.Count -gt 0) { $kitAfter[-1] } else { $null }
    $copiedKit = ''
    if ($latestKit -and ($kitBefore.Count -eq 0 -or $latestKit.LastWriteTime -ge $start)) {
        $copiedKit = Join-Path $DiagRoot "kit_logs\$attemptId`_$($latestKit.Name)"
        Copy-Item -LiteralPath $latestKit.FullName -Destination $copiedKit
    }
    $resultPath = Join-Path $output 'result.json'
    $passed = $false
    if (Test-Path -LiteralPath $resultPath -PathType Leaf) {
        try { $passed = [bool]((Get-Content -Raw -LiteralPath $resultPath | ConvertFrom-Json).passed) } catch { $passed = $false }
    }
    $attempts.Add([pscustomobject]@{
        attempt_id = $attemptId
        mode = $Mode
        command = $command
        working_directory = $IsaacLabRoot
        parent_pid = $PID
        child_pid = if ($proc) { $proc.Id } else { '' }
        started_at = $start.ToString('o')
        ended_at = $end.ToString('o')
        exit_code = $exitCode
        duration_s = [math]::Round(($end - $start).TotalSeconds,3)
        stdout_path = $stdout
        stderr_path = $stderr
        kit_log_path = $copiedKit
        result_path = $resultPath
        status = if ($passed -and $exitCode -eq 0) { 'COMPLETED' } elseif ($passed) { 'COMPLETED_RENDER_SHUTDOWN_TIMEOUT' } else { 'FAILED' }
    })
}

if (-not $SkipVisibleSmoke) { Invoke-IsaacSmoke -Mode visible }
if (-not $SkipOffscreenSmoke) { Invoke-IsaacSmoke -Mode offscreen }

$attempts | Export-Csv -LiteralPath (Join-Path $ReportRoot 'startup_attempts.csv') -NoTypeInformation -Encoding utf8
Save-ProcessSnapshot -Name 'after_diagnosis'

$Python = 'C:\Users\kskzz\miniconda3\envs\env_isaaclab\python.exe'
& $Python (Join-Path $ProjectRoot 'tools\visualization\diagnose_isaac_startup.py') --report-root $ReportRoot --windows-events $eventPath
if ($LASTEXITCODE -ne 0) { throw 'Static startup diagnosis failed.' }

$current = @($attempts | Where-Object { $_.mode -in @('visible','offscreen') })
$visible = @($current | Where-Object mode -eq 'visible' | Select-Object -Last 1)
$offscreen = @($current | Where-Object mode -eq 'offscreen' | Select-Object -Last 1)
$extra = @"

## Current minimal smoke results

- Visible smoke: **$(if ($visible.Count) { $visible[0].status } else { 'SKIPPED' })**; exit code: $(if ($visible.Count) { $visible[0].exit_code } else { 'n/a' }).
- Headless/offscreen camera smoke: **$(if ($offscreen.Count) { $offscreen[0].status } else { 'SKIPPED' })**; exit code: $(if ($offscreen.Count) { $offscreen[0].exit_code } else { 'n/a' }).
- Visible GUI fixed: **$(if ($visible.Count -and $visible[0].status -eq 'COMPLETED') { 'minimal startup verified; controller viewer not yet claimed fixed' } else { 'no' })**.
- Offscreen recorder prerequisite stable: **$(if ($offscreen.Count -and $offscreen[0].status -eq 'COMPLETED') { 'yes' } else { 'not yet verified' })**.
"@
Add-Content -LiteralPath (Join-Path $ReportRoot 'CRASH_DIAGNOSIS.md') -Value $extra -Encoding utf8

Write-Output "Startup diagnosis complete: $(Join-Path $ReportRoot 'CRASH_DIAGNOSIS.md')"
Write-Output "REPORT_ROOT=$ReportRoot"
