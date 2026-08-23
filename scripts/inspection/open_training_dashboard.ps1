[CmdletBinding()]
param(
    [ValidateRange(1024,65535)][int]$Port = 6006,
    [switch]$DryRun
)

. (Join-Path $PSScriptRoot 'inspection_common.ps1')

$b = Join-Path $script:ProjectRoot 'runs\ppo_without_com\training'
$c = Join-Path $script:ProjectRoot 'runs\ppo_with_com\training'
$logdirSpec = "MethodB:$b,MethodC:$c"
$args = @('run','--no-capture-output','-n','env_isaaclab','python','-m','tensorboard.main','--logdir_spec',$logdirSpec,'--port',[string]$Port,'--host','127.0.0.1')
$safety = Get-InspectionSafety
Write-Host "Launch safe now: $($safety.Safe)"
Write-Host (Format-InspectionCommand (@('conda') + $args))
Write-Host "URL: http://127.0.0.1:$Port"
if ($DryRun) { return }
Assert-InspectionLaunchSafe
Start-Process -WindowStyle Hidden -FilePath $script:CondaExe -ArgumentList $args -WorkingDirectory $script:ProjectRoot
