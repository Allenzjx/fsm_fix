param(
    [string]$RuntimeVersion = "v34",
    [int]$LockedAttempt = 1,
    [int]$VideoAttempt = 1
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$FreezePath = Join-Path $ProjectRoot "configs\method_freeze.json"
if (-not (Test-Path -LiteralPath $FreezePath -PathType Leaf)) {
    throw "Method freeze is missing"
}
$FreezeHash = (
    Get-FileHash -LiteralPath $FreezePath -Algorithm SHA256
).Hash.ToLowerInvariant()
$LockedRoot = Join-Path $ProjectRoot (
    "runs\locked_test\runtime-$RuntimeVersion`_freeze-$($FreezeHash.Substring(0,12))" +
    "_attempt$('{0:D3}' -f $LockedAttempt)"
)
$Authorization = Join-Path $LockedRoot "locked_test_authorization.json"
$Audit = Join-Path $LockedRoot "paired_coverage_audit.json"
$VideosRoot = Join-Path $ProjectRoot (
    "reports\videos\runtime-$RuntimeVersion`_freeze-$($FreezeHash.Substring(0,12))" +
    "_locked$('{0:D3}' -f $LockedAttempt)_video$('{0:D3}' -f $VideoAttempt)"
)
$VideoInventory = Join-Path $VideosRoot "video_inventory.json"
$ReportsRoot = Join-Path $ProjectRoot "reports"
$OutputJson = Join-Path $ReportsRoot "final_audit.json"
$OutputMarkdown = Join-Path $ReportsRoot "final_audit.md"
$Python = "C:\Users\kskzz\miniconda3\envs\env_isaaclab\python.exe"
$PreviousPythonPath = $env:PYTHONPATH
$SourceRoot = Join-Path $ProjectRoot "src"
$env:PYTHONPATH = if ([string]::IsNullOrWhiteSpace($PreviousPythonPath)) {
    $SourceRoot
} else {
    "$SourceRoot$([IO.Path]::PathSeparator)$PreviousPythonPath"
}

try {
    Push-Location $ProjectRoot
    try {
        & $Python -m resume_validation.final_audit `
            --project_root $ProjectRoot `
            --freeze $FreezePath `
            --authorization $Authorization `
            --locked_run_root $LockedRoot `
            --recorded_audit $Audit `
            --video_inventory $VideoInventory `
            --reports_root $ReportsRoot `
            --output_json $OutputJson `
            --output_markdown $OutputMarkdown
        if ($LASTEXITCODE -ne 0) {
            throw "Final delivery audit failed"
        }
    } finally {
        Pop-Location
    }
} finally {
    $env:PYTHONPATH = $PreviousPythonPath
}

Write-Output "Final delivery audit passed: $OutputJson"

