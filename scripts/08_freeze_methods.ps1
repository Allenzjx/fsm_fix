param(
    [string]$RuntimeVersion = "v34",
    [int]$ValidationAttempt = 1
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ValidationRoot = Join-Path $ProjectRoot (
    "runs\validation\runtime-$RuntimeVersion`_attempt$('{0:D3}' -f $ValidationAttempt)"
)
$FreezePath = Join-Path $ProjectRoot "configs\method_freeze.json"
$PreviousPythonPath = $env:PYTHONPATH
$SourceRoot = Join-Path $ProjectRoot "src"
$env:PYTHONPATH = if ([string]::IsNullOrWhiteSpace($PreviousPythonPath)) {
    $SourceRoot
} else {
    "$SourceRoot$([IO.Path]::PathSeparator)$PreviousPythonPath"
}

try {
    & conda run --no-capture-output -n env_isaaclab python -m resume_validation.method_freeze `
        create `
        --project_root $ProjectRoot `
        --validation_root $ValidationRoot `
        --runtime_version $RuntimeVersion `
        --output $FreezePath
    if ($LASTEXITCODE -ne 0) {
        throw "Method freeze failed; locked-test access remains unauthorized"
    }
} finally {
    $env:PYTHONPATH = $PreviousPythonPath
}
