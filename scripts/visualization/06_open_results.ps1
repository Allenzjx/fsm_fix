[CmdletBinding()]
param([string]$ReportRoot = '')

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
if (-not $ReportRoot) {
    $ReportRoot = Get-ChildItem -LiteralPath (Join-Path $ProjectRoot 'reports') -Directory -Filter 'visualization_capture_*' |
        Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName 'index.html') } |
        Sort-Object Name | Select-Object -Last 1 -ExpandProperty FullName
}
if (-not $ReportRoot) { throw 'No completed visualization index exists. Run 05_build_video_index.ps1 first.' }
$Index = Join-Path $ReportRoot 'index.html'
$Videos = Join-Path $ReportRoot 'videos'
if (-not (Test-Path -LiteralPath $Index -PathType Leaf)) { throw "Missing index: $Index" }
Start-Process -FilePath $Index
Start-Process -FilePath $Videos
Write-Output "Opened recorded results only: $ReportRoot"
