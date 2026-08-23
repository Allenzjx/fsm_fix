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
$FreezeHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $FreezePath).Hash.ToLower()
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
if (
    -not (Test-Path -LiteralPath $Authorization -PathType Leaf) -or
    -not (Test-Path -LiteralPath $Audit -PathType Leaf) -or
    -not (Test-Path -LiteralPath $VideoInventory -PathType Leaf)
) {
    throw "Locked campaign or video inventory is incomplete"
}
$ReportsRoot = Join-Path $ProjectRoot "reports"
$UnitTestXml = Join-Path $ReportsRoot "unit_test_results.xml"
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
        if (Test-Path -LiteralPath $UnitTestXml) {
            $ExistingUnitAudit = [xml](Get-Content -LiteralPath $UnitTestXml -Raw)
            $ExistingRoot = $ExistingUnitAudit.DocumentElement
            if (
                [int]$ExistingRoot.tests -lt 1 -or
                [int]$ExistingRoot.failures -ne 0 -or
                [int]$ExistingRoot.errors -ne 0
            ) {
                throw "Preserved final unit-test audit is failed: $UnitTestXml"
            }
        } else {
            & $Python -m pytest -q --junitxml $UnitTestXml
            if ($LASTEXITCODE -ne 0) {
                throw "Final unit regression failed; reports were not generated"
            }
        }
        & $Python -m resume_validation.report_generator `
            --project_root $ProjectRoot `
            --freeze $FreezePath `
            --authorization $Authorization `
            --locked_run_root $LockedRoot `
            --audit $Audit `
            --video_inventory $VideoInventory `
            --reports_root $ReportsRoot `
            --unit_test_xml $UnitTestXml
        if ($LASTEXITCODE -ne 0) {
            throw "Final report generation failed"
        }
    } finally {
        Pop-Location
    }
} finally {
    $env:PYTHONPATH = $PreviousPythonPath
}
