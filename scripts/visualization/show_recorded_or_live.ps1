[CmdletBinding()]
param(
    [switch]$Live,
    [ValidateSet(50,75,100)][int]$HeightMm = 50,
    [string]$ReportRoot = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if (-not $Live) {
    & (Join-Path $PSScriptRoot '06_open_results.ps1') -ReportRoot $ReportRoot
    return
}

# Live mode is intentionally explicit and limited to one frozen-FSM viewer.
# It never starts training and never uses a locked manifest.
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
& (Join-Path $ProjectRoot 'scripts\inspection\show_fsm_gui.ps1') -HeightMm $HeightMm -ScenarioMode nominal
