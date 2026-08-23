$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$env:PYTHONPATH = Join-Path $ProjectRoot "src"

Push-Location $ProjectRoot
try {
    conda run --no-capture-output -n env_isaaclab python -m resume_validation.cli inventory
    if ($LASTEXITCODE -ne 0) { throw "Inventory failed with exit code $LASTEXITCODE" }
    conda run --no-capture-output -n env_isaaclab python -m resume_validation.cli asset-audit
    if ($LASTEXITCODE -ne 0) { throw "URDF audit failed with exit code $LASTEXITCODE" }
    conda run --no-capture-output -n env_isaaclab python -m resume_validation.cli analyze-replays
    if ($LASTEXITCODE -ne 0) { throw "Replay parsing failed with exit code $LASTEXITCODE" }
    conda run --no-capture-output -n env_isaaclab python -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw "Unit tests failed with exit code $LASTEXITCODE" }
} finally {
    Pop-Location
}
