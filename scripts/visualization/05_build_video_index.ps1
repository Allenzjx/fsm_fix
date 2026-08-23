[CmdletBinding()]
param([string]$ReportRoot = '')

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$Python = 'C:\Users\kskzz\miniconda3\envs\env_isaaclab\python.exe'
if (-not $ReportRoot) {
    $ReportRoot = Get-ChildItem -LiteralPath (Join-Path $ProjectRoot 'reports') -Directory -Filter 'visualization_capture_*' |
        Sort-Object Name | Select-Object -Last 1 -ExpandProperty FullName
}
if (-not $ReportRoot) { throw 'No visualization_capture report exists.' }
& $Python (Join-Path $ProjectRoot 'tools\visualization\build_video_index.py') --report-root $ReportRoot --index
if ($LASTEXITCODE -ne 0) { throw 'Video index generation failed.' }
Write-Output "Video index complete: $(Join-Path $ReportRoot 'index.html')"
