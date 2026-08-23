[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidateSet(50,75,100)][int]$HeightMm,
    [string]$ScenarioId = '',
    [ValidateSet('nominal','development-success','development-failure')][string]$ScenarioMode = 'nominal',
    [switch]$RecordVideo,
    [switch]$DryRun,
    [string]$OutputDir = ''
)

. (Join-Path $PSScriptRoot 'inspection_common.ps1')

$scenario = Resolve-InspectionScenario -HeightMm $HeightMm -ScenarioId $ScenarioId -ScenarioMode $ScenarioMode -EvidenceEpisodes (Get-FsmEvidenceEpisodes $HeightMm)
if (-not $OutputDir) { $OutputDir = Get-UniqueInspectionOutput "fsm_${HeightMm}mm_$scenario" }
if (Test-Path -LiteralPath $OutputDir) { throw "Refusing to overwrite existing output directory: $OutputDir" }
$evalArgs = @('--controller','fsm','--manifest',$script:DevelopmentManifest,'--height_mm',[string]$HeightMm,'--output_dir',$OutputDir,'--scenario_id',$scenario)
if ($RecordVideo) { $evalArgs += @('--enable_cameras','--video_path',(Join-Path $OutputDir 'fsm.mp4'),'--video_category','inspection-development') }
$previewArgs = @('conda','run','--no-capture-output','-n','env_isaaclab','.\isaaclab.bat','-p',$script:Evaluator) + $evalArgs
$safety = Get-InspectionSafety
Write-Host "Controller: frozen FSM (SHA256=$(Get-Sha256Lower (Join-Path $script:ProjectRoot 'configs\fsm.yaml')))"
Write-Host "Scenario: $scenario; height: $HeightMm mm; output: $OutputDir"
Write-Host "Launch safe now: $($safety.Safe)"
Write-Host (Format-InspectionCommand $previewArgs)
if ($DryRun) { return }
Assert-InspectionLaunchSafe
New-Item -ItemType Directory -Path $OutputDir | Out-Null
$log = Join-Path $OutputDir 'viewer.log'
Push-Location $script:IsaacLabRoot
try { & $script:CondaExe @($previewArgs[1..($previewArgs.Count-1)]) 2>&1 | Tee-Object -FilePath $log; if ($LASTEXITCODE -ne 0) { throw "FSM viewer exited with code $LASTEXITCODE" } }
finally { Pop-Location }
