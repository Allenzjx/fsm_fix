param(
    [int]$SettleSteps = 600,
    [int]$MotionSteps = 120
)
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$IsaacLabRoot = "C:\robotics_sim\IsaacLab"
$Asset = Join-Path $ProjectRoot "assets\converted\wlr_robot_validation.usd"
$Output = Join-Path $ProjectRoot "assets\validation\isaac_integration_latest.json"

Push-Location $IsaacLabRoot
try {
    conda run --no-capture-output -n env_isaaclab .\isaaclab.bat -p `
        (Join-Path $ProjectRoot "src\resume_validation\isaac_validation.py") `
        --robot_usd $Asset --settle_steps $SettleSteps --motion_steps $MotionSteps `
        --output $Output --headless
    if ($LASTEXITCODE -ne 0) { throw "Asset integration validation failed with exit code $LASTEXITCODE" }
} finally {
    Pop-Location
}
