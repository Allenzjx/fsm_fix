param(
    [ValidateSet(50, 100, 0)]
    [int]$HeightMm = 0,
    [int]$RecordEvery = 3,
    [int]$Seed = 20260727,
    [ValidateSet("raw", "fast")]
    [string]$Profile = "raw"
)
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$IsaacLabRoot = "C:\robotics_sim\IsaacLab"
$Heights = if ($HeightMm -eq 0) { @(50, 100) } else { @($HeightMm) }
$RunStamp = Get-Date -Format "yyyyMMdd_HHmmss"

Push-Location $IsaacLabRoot
try {
    foreach ($Height in $Heights) {
        $Output = Join-Path $ProjectRoot ("runs\replay\replay_{0}mm_{1}" -f $Height, $RunStamp)
        conda run --no-capture-output -n env_isaaclab .\isaaclab.bat -p `
            (Join-Path $ProjectRoot "src\resume_validation\replay_direct_validation.py") `
            --height_mm $Height --seed $Seed --profile $Profile `
            --output_dir $Output --record_every $RecordEvery --headless
        $ResultPath = Join-Path $Output "result.json"
        if (-not (Test-Path -LiteralPath $ResultPath)) {
            throw "Physical replay for ${Height}mm produced no result.json. See $Output"
        }
        $Result = Get-Content -LiteralPath $ResultPath -Raw | ConvertFrom-Json
        if (-not [bool]$Result.passed) {
            throw "Physical replay for ${Height}mm failed recorded checks. See $ResultPath"
        }
    }
} finally {
    Pop-Location
}
