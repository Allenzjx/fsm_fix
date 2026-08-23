param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("B", "C")]
    [string]$Method,
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
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$IsaacLabRoot = "C:\robotics_sim\IsaacLab"
$MethodFolder = if ($Method -eq "B") { "ppo_without_com" } else { "ppo_with_com" }
$OutputRoot = Join-Path $ProjectRoot "runs\$MethodFolder\training"
$GateRoot = Join-Path $ProjectRoot "runs\$MethodFolder\development_gates"
$Manifest = Join-Path $ProjectRoot "data\scenario_manifests\development_v2.json"
$Trainer = Join-Path $ProjectRoot "src\resume_validation\train_residual_ppo.py"
$Evaluator = Join-Path $ProjectRoot "src\resume_validation\evaluate_controller.py"
$GateChecker = Join-Path $ProjectRoot "src\resume_validation\curriculum_gate.py"
$CommonConfig = Join-Path $ProjectRoot "configs\ppo_common.yaml"

New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null
New-Item -ItemType Directory -Path $GateRoot -Force | Out-Null

$SeedOrder = @(11, 29, 47)
$HeightOrder = @(50, 75, 100)
$StartSeedIndex = [Array]::IndexOf($SeedOrder, $StartSeed)
if ($StartSeedIndex -lt 0) {
    throw "Unsupported start seed: $StartSeed"
}
if ($StartHeight -ne 50) {
    if ([string]::IsNullOrWhiteSpace($InitialResumeCheckpoint)) {
        throw "-InitialResumeCheckpoint is required when -StartHeight is $StartHeight"
    }
    if (-not (Test-Path -LiteralPath $InitialResumeCheckpoint -PathType Leaf)) {
        throw "Initial resume checkpoint does not exist: $InitialResumeCheckpoint"
    }
} elseif (-not [string]::IsNullOrWhiteSpace($InitialResumeCheckpoint)) {
    throw "-InitialResumeCheckpoint is only valid when -StartHeight is 75 or 100"
}

Push-Location $IsaacLabRoot
try {
    for ($SeedIndex = $StartSeedIndex; $SeedIndex -lt $SeedOrder.Count; $SeedIndex++) {
        $Seed = $SeedOrder[$SeedIndex]
        $FirstSeedInThisInvocation = $SeedIndex -eq $StartSeedIndex
        $ResumeCheckpoint = if ($FirstSeedInThisInvocation -and $StartHeight -ne 50) {
            (Resolve-Path -LiteralPath $InitialResumeCheckpoint).Path
        } else {
            $null
        }
        $HeightsForSeed = if ($FirstSeedInThisInvocation) {
            $HeightOrder | Where-Object { $_ -ge $StartHeight }
        } else {
            $HeightOrder
        }
        foreach ($Height in $HeightsForSeed) {
            $RandomizationLevel = if ($Height -eq 50) {
                "full"
            } elseif ($Height -eq 75) {
                "light"
            } else {
                "full"
            }
            $RunName = "method-$Method-$RuntimeVersion`_seed-$Seed`_stage-${Height}mm_attempt$('{0:D3}' -f $Attempt)"
            $RunDir = Join-Path $OutputRoot $RunName
            $FinalCheckpoint = Join-Path $RunDir "checkpoints\final_agent.pt"
            $TrainingResult = Join-Path $RunDir "training_result.json"

            if (-not (Test-Path -LiteralPath $FinalCheckpoint)) {
                if (Test-Path -LiteralPath $RunDir) {
                    throw "Incomplete run directory already exists; preserve it and increment -Attempt: $RunDir"
                }
                $TrainArgs = @(
                    "run", "--no-capture-output", "-n", "env_isaaclab",
                    ".\isaaclab.bat", "-p", $Trainer,
                    "--method", $Method,
                    "--seed", $Seed,
                    "--height_mm", $Height,
                    "--iterations", $Iterations,
                    "--num_envs", $NumEnvs,
                    "--rollouts", $Rollouts,
                    "--randomization_level", $RandomizationLevel,
                    "--run_name", $RunName,
                    "--output_root", $OutputRoot,
                    "--headless"
                )
                if ($null -ne $ResumeCheckpoint) {
                    # This is a cross-curriculum-stage warm start. The trainer's
                    # resume_offset_timesteps parameter is reserved for recovery
                    # inside the same height stage and must remain zero here.
                    $TrainArgs += @("--resume", $ResumeCheckpoint)
                }
                & conda @TrainArgs
                if ($LASTEXITCODE -ne 0) {
                    throw "Method $Method training failed: seed=$Seed height=${Height}mm exit=$LASTEXITCODE"
                }
            }
            if (-not (Test-Path -LiteralPath $TrainingResult) -or -not (Test-Path -LiteralPath $FinalCheckpoint)) {
                throw "Training artifacts are incomplete: $RunDir"
            }
            $Training = Get-Content -LiteralPath $TrainingResult -Raw | ConvertFrom-Json
            if ($Training.status -ne "COMPLETED") {
                throw "Training result is not COMPLETED: $TrainingResult"
            }

            $GateDir = Join-Path $GateRoot $RunName
            $GateResult = Join-Path $GateDir "result.json"
            if (-not (Test-Path -LiteralPath $GateResult)) {
                if (Test-Path -LiteralPath $GateDir) {
                    throw "Incomplete gate directory already exists; preserve it and increment -Attempt: $GateDir"
                }
                & conda run --no-capture-output -n env_isaaclab .\isaaclab.bat -p $Evaluator `
                    --controller $Method `
                    --checkpoint $FinalCheckpoint `
                    --manifest $Manifest `
                    --height_mm $Height `
                    --output_dir $GateDir `
                    --headless
                if ($LASTEXITCODE -ne 0) {
                    throw "Development gate execution failed: method=$Method seed=$Seed height=${Height}mm"
                }
            }
            $Gate = Get-Content -LiteralPath $GateResult -Raw | ConvertFrom-Json
            if (-not $Gate.passed_execution) {
                throw "Development gate did not complete: $GateResult"
            }
            $GateDecision = Join-Path $GateDir "gate_decision.json"
            & conda run --no-capture-output -n env_isaaclab .\isaaclab.bat -p $GateChecker `
                --evaluation $GateResult `
                --checkpoint $FinalCheckpoint `
                --common_config $CommonConfig `
                --method $Method `
                --seed $Seed `
                --height_mm $Height `
                --output $GateDecision
            if ($LASTEXITCODE -ne 0) {
                if ($LASTEXITCODE -eq 2 -and $ContinueAfterFailedGate) {
                    Write-Warning (
                        "Development ideal not reached; preserving the failed " +
                        "gate and continuing the fixed complete-comparison " +
                        "schedule: $GateDecision"
                    )
                } else {
                    throw "Curriculum promotion blocked; inspect $GateDecision"
                }
            }
            $ResumeCheckpoint = $FinalCheckpoint
        }
    }
} finally {
    Pop-Location
}
