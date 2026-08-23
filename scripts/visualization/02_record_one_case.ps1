[CmdletBinding()]
param(
    [string]$CaseId = '',
    [ValidateSet('fsm','B','C')][string]$Controller = 'fsm',
    [ValidateSet(50,75,100)][int]$HeightMm = 50,
    [ValidateSet('success','failure')][string]$Outcome = 'success',
    [string]$ReportRoot = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$Python = 'C:\Users\kskzz\miniconda3\envs\env_isaaclab\python.exe'
$Recorder = Join-Path $ProjectRoot 'tools\visualization\record_existing_controller.py'
if (-not $ReportRoot) {
    $ReportRoot = Get-ChildItem -LiteralPath (Join-Path $ProjectRoot 'reports') -Directory -Filter 'visualization_capture_*' |
        Sort-Object Name | Select-Object -Last 1 -ExpandProperty FullName
}
if (-not $ReportRoot) { throw 'No visualization_capture report exists. Run 01_diagnose_isaac_startup.ps1 first.' }

& $Python $Recorder --report-root $ReportRoot --plan-only | Out-Null
$Plan = Get-Content -Raw -LiteralPath (Join-Path $ReportRoot 'capture_plan.json') | ConvertFrom-Json
if (-not $CaseId) {
    $matches = @($Plan | Where-Object {
        $_.controller -eq $Controller -and [int]$_.height_mm -eq $HeightMm -and $_.requested_outcome -eq $Outcome
    })
    if ($matches.Count -ne 1) { throw "Expected one capture case for $Controller/$HeightMm/$Outcome; found $($matches.Count)." }
    $CaseId = $matches[0].case_id
}
if (-not @($Plan | Where-Object case_id -eq $CaseId).Count) { throw "Unknown primary case: $CaseId" }

& $Python $Recorder --report-root $ReportRoot --case-id $CaseId
if ($LASTEXITCODE -ne 0) { throw "Capture failed for $CaseId. Diagnostics were preserved; a later batch can resume." }
Write-Output "Recorded and verified: $CaseId"
Write-Output "REPORT_ROOT=$ReportRoot"
