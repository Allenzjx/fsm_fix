param(
    [int]$Iterations = 1200,
    [int]$NumEnvs = 64,
    [int]$Rollouts = 64,
    [int]$Attempt = 1,
    [string]$RuntimeVersion = "v34",
    [ValidateSet(11, 29, 47)]
    [int]$StartSeed = 11,
    [ValidateSet(50, 75, 100)]
    [int]$StartHeight = 50,
    [string]$InitialResumeCheckpoint = "",
    [switch]$ContinueAfterFailedGate
)
$ErrorActionPreference = "Stop"
& (Join-Path $PSScriptRoot "train_curriculum.ps1") `
    -Method B -Iterations $Iterations -NumEnvs $NumEnvs -Rollouts $Rollouts `
    -Attempt $Attempt -RuntimeVersion $RuntimeVersion `
    -StartSeed $StartSeed -StartHeight $StartHeight `
    -InitialResumeCheckpoint $InitialResumeCheckpoint `
    -ContinueAfterFailedGate:$ContinueAfterFailedGate
