param(
    [ValidateSet(50, 75, 100, 0)]
    [int]$HeightMm = 0,
    [int]$ScenarioLimit = 1,
    [int]$MaxEpisodeSeconds = 150
)
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$IsaacLabRoot = "C:\robotics_sim\IsaacLab"
$Manifest = Join-Path $ProjectRoot "data\scenario_manifests\development_v2.json"
$Heights = if ($HeightMm -eq 0) { @(50, 75, 100) } else { @($HeightMm) }
$RunStamp = Get-Date -Format "yyyyMMdd_HHmmss"

Push-Location $IsaacLabRoot
try {
    foreach ($Height in $Heights) {
        $Output = Join-Path $ProjectRoot ("runs\fsm\development_{0}mm_{1}" -f $Height, $RunStamp)
        $Arguments = @(
            "--controller", "fsm",
            "--manifest", $Manifest,
            "--height_mm", $Height,
            "--max_episode_s", $MaxEpisodeSeconds,
            "--output_dir", $Output,
            "--headless"
        )
        if ($ScenarioLimit -gt 0) {
            $Arguments += @("--limit", $ScenarioLimit)
        }
        conda run --no-capture-output -n env_isaaclab .\isaaclab.bat -p `
            (Join-Path $ProjectRoot "src\resume_validation\evaluate_controller.py") @Arguments
        $ResultPath = Join-Path $Output "result.json"
        if (-not (Test-Path -LiteralPath $ResultPath)) {
            throw "FSM development run produced no result: $Output"
        }
        $Result = Get-Content -LiteralPath $ResultPath -Raw | ConvertFrom-Json
        if (-not [bool]$Result.passed_execution) {
            throw "FSM development execution failed. See $ResultPath"
        }
    }
} finally {
    Pop-Location
}
