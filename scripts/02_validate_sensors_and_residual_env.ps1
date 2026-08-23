param(
    [int]$NumEnvs = 16,
    [int]$SettleSteps = 180,
    [int]$ZeroSteps = 300,
    [int]$RandomSteps = 40
)
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$IsaacLabRoot = "C:\robotics_sim\IsaacLab"
$Output = Join-Path $ProjectRoot "assets\validation\residual_env_validation_latest.json"

Push-Location $IsaacLabRoot
try {
    conda run --no-capture-output -n env_isaaclab .\isaaclab.bat -p `
        (Join-Path $ProjectRoot "src\resume_validation\validate_residual_env.py") `
        --num_envs $NumEnvs --settle_steps $SettleSteps --zero_steps $ZeroSteps `
        --random_steps $RandomSteps --output $Output --headless
    if ($LASTEXITCODE -ne 0) { throw "Sensor/residual environment validation failed with exit code $LASTEXITCODE" }
    conda run --no-capture-output -n env_isaaclab .\isaaclab.bat -p `
        (Join-Path $ProjectRoot "src\resume_validation\validate_runtime_fk.py") `
        --output (Join-Path $ProjectRoot "assets\validation\runtime_fk_validation_latest.json") --headless
    if ($LASTEXITCODE -ne 0) { throw "Runtime FK validation failed with exit code $LASTEXITCODE" }
} finally {
    Pop-Location
}
