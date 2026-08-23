[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidateSet('B','C')][string]$Method,
    [Parameter(Mandatory)][int]$Seed,
    [Parameter(Mandatory)][ValidateSet(50,75,100)][int]$HeightMm,
    [string]$Checkpoint = 'auto',
    [string]$ScenarioId = '',
    [ValidateSet('nominal','development-success','development-failure')][string]$ScenarioMode = 'nominal',
    [switch]$RecordVideo,
    [switch]$DryRun,
    [string]$OutputDir = ''
)

. (Join-Path $PSScriptRoot 'inspection_common.ps1')

$run = Get-FormalControllerRun -Method $Method -Seed $Seed -HeightMm $HeightMm -RequireCompleted
$gateDir = Join-Path $script:ProjectRoot "runs\$($run.Folder)\development_gates\$($run.Name)"
$gatePath = Join-Path $gateDir 'gate_decision.json'
$gate = if (Test-Path -LiteralPath $gatePath) { Get-Content -LiteralPath $gatePath -Raw | ConvertFrom-Json } else { $null }
switch ($Checkpoint.ToLowerInvariant()) {
    'auto' {
        if (-not $gate -or -not [bool]$gate.promote) { throw "Auto selection refused: $($run.Name) has no promoted development checkpoint. Specify -Checkpoint best or final explicitly for diagnostic viewing." }
        $checkpointPath = [string]$gate.checkpoint
    }
    'best' { $checkpointPath = Join-Path $run.Directory 'checkpoints\best_agent.pt' }
    'final' { $checkpointPath = Join-Path $run.Directory 'checkpoints\final_agent.pt' }
    default { $checkpointPath = $Checkpoint }
}
if (-not (Test-Path -LiteralPath $checkpointPath -PathType Leaf)) { throw "Requested checkpoint does not exist: $checkpointPath. No fallback is permitted." }
$episodes = Join-Path $gateDir 'episodes.jsonl'
$scenario = Resolve-InspectionScenario -HeightMm $HeightMm -ScenarioId $ScenarioId -ScenarioMode $ScenarioMode -EvidenceEpisodes $episodes
if (-not $OutputDir) { $OutputDir = Get-UniqueInspectionOutput "ppo_${Method}_seed${Seed}_${HeightMm}mm_$scenario" }
if (Test-Path -LiteralPath $OutputDir) { throw "Refusing to overwrite existing output directory: $OutputDir" }
$evalArgs = @('--controller',$Method,'--checkpoint',$checkpointPath,'--manifest',$script:DevelopmentManifest,'--height_mm',[string]$HeightMm,'--output_dir',$OutputDir,'--scenario_id',$scenario)
if ($RecordVideo) { $evalArgs += @('--enable_cameras','--video_path',(Join-Path $OutputDir "method_${Method}.mp4"),'--video_category','inspection-development') }
$previewArgs = @('conda','run','--no-capture-output','-n','env_isaaclab','.\isaaclab.bat','-p',$script:Evaluator) + $evalArgs
$safety = Get-InspectionSafety
Write-Host "Controller: Method $Method; run: $($run.Name); training status: $($run.Result.status)"
Write-Host "Checkpoint: $checkpointPath; SHA256=$(Get-Sha256Lower $checkpointPath)"
Write-Host "Scenario: $scenario; height: $HeightMm mm; deterministic playback: mean_actions"
Write-Host "Launch safe now: $($safety.Safe); output: $OutputDir"
Write-Host (Format-InspectionCommand $previewArgs)
if ($DryRun) { return }
Assert-InspectionLaunchSafe
New-Item -ItemType Directory -Path $OutputDir | Out-Null
$log = Join-Path $OutputDir 'viewer.log'
Push-Location $script:IsaacLabRoot
try { & $script:CondaExe @($previewArgs[1..($previewArgs.Count-1)]) 2>&1 | Tee-Object -FilePath $log; if ($LASTEXITCODE -ne 0) { throw "PPO viewer exited with code $LASTEXITCODE" } }
finally { Pop-Location }
