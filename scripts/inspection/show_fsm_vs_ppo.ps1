[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidateSet('B','C')][string]$Method,
    [Parameter(Mandatory)][int]$Seed,
    [Parameter(Mandatory)][ValidateSet(50,75,100)][int]$HeightMm,
    [string]$Checkpoint = 'auto',
    [string]$ScenarioId = '',
    [ValidateSet('nominal','development-success','development-failure')][string]$ScenarioMode = 'nominal',
    [switch]$RecordVideo,
    [switch]$SideBySide,
    [switch]$DryRun
)

. (Join-Path $PSScriptRoot 'inspection_common.ps1')

$scenario = Resolve-InspectionScenario -HeightMm $HeightMm -ScenarioId $ScenarioId -ScenarioMode $ScenarioMode -EvidenceEpisodes (Get-FsmEvidenceEpisodes $HeightMm)
$base = Get-UniqueInspectionOutput "fsm_vs_${Method}_seed${Seed}_${HeightMm}mm_$scenario"
Write-Host "Shared development scenario: $scenario"
Write-Host 'Runs are sequential, never simultaneous: FSM first, then PPO.'
if ($SideBySide -and -not $RecordVideo) { throw '-SideBySide requires -RecordVideo.' }
if (-not $DryRun) { Assert-InspectionLaunchSafe }
& (Join-Path $PSScriptRoot 'show_fsm_gui.ps1') -HeightMm $HeightMm -ScenarioId $scenario -ScenarioMode nominal -RecordVideo:$RecordVideo -DryRun:$DryRun -OutputDir (Join-Path $base 'fsm')
& (Join-Path $PSScriptRoot 'show_ppo_gui.ps1') -Method $Method -Seed $Seed -HeightMm $HeightMm -Checkpoint $Checkpoint -ScenarioId $scenario -ScenarioMode nominal -RecordVideo:$RecordVideo -DryRun:$DryRun -OutputDir (Join-Path $base "method_$Method")
if ($DryRun) {
    if ($RecordVideo) { Write-Host "Two comparable videos would be written below $base; no result is labeled formal or locked." }
    return
}
$fsmResultPath = Join-Path $base 'fsm\result.json'
$ppoResultPath = Join-Path $base "method_$Method\result.json"
if (-not (Test-Path -LiteralPath $fsmResultPath) -or -not (Test-Path -LiteralPath $ppoResultPath)) {
    throw 'Both sequential evaluations returned, but one or both result.json files are missing.'
}
$fsmResult = Get-Content -LiteralPath $fsmResultPath -Raw | ConvertFrom-Json
$ppoResult = Get-Content -LiteralPath $ppoResultPath -Raw | ConvertFrom-Json
$summary = [ordered]@{
    label = 'DIAGNOSTIC_ONLY_NOT_FORMAL_OR_LOCKED'
    scenario_id = $scenario
    height_mm = $HeightMm
    fsm = $fsmResult.aggregate
    ppo_method = $Method
    ppo = $ppoResult.aggregate
    fsm_result = $fsmResultPath
    ppo_result = $ppoResultPath
}
$summaryPath = Join-Path $base 'comparison_summary.json'
[IO.File]::WriteAllText($summaryPath, ($summary | ConvertTo-Json -Depth 8), [Text.UTF8Encoding]::new($false))
Write-Host 'Unified diagnostic result summary:'
$summary | ConvertTo-Json -Depth 8
if ($RecordVideo) { Write-Host "Two comparable videos were written below $base; no result is labeled formal or locked." }
if ($SideBySide) {
    $ffmpeg = Get-Command ffmpeg -ErrorAction SilentlyContinue
    if (-not $ffmpeg) { Write-Warning 'ffmpeg is unavailable; the two source videos remain available but side-by-side output was not created.' }
    else {
        $fsmVideo = Join-Path $base 'fsm\fsm.mp4'
        $ppoVideo = Join-Path $base "method_$Method\method_$Method.mp4"
        $combined = Join-Path $base 'side_by_side.mp4'
        & $ffmpeg.Source -n -i $fsmVideo -i $ppoVideo -filter_complex '[0:v][1:v]hstack=inputs=2[v]' -map '[v]' -an $combined
        if ($LASTEXITCODE -ne 0) { throw "ffmpeg side-by-side generation exited with code $LASTEXITCODE" }
        Write-Host "Side-by-side video: $combined"
    }
}
