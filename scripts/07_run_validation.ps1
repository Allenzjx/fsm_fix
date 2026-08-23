param(
    [string]$RuntimeVersion = "v34",
    [int]$ValidationAttempt = 1
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$IsaacLabRoot = "C:\robotics_sim\IsaacLab"
$Evaluator = Join-Path $ProjectRoot "src\resume_validation\evaluate_controller.py"
$Manifest = Join-Path $ProjectRoot "data\scenario_manifests\validation_v2.json"
$Protocol = Join-Path $ProjectRoot "configs\validation_selection_protocol.json"
$FreezePath = Join-Path $ProjectRoot "configs\method_freeze.json"
$ValidationRoot = Join-Path $ProjectRoot (
    "runs\validation\runtime-$RuntimeVersion`_attempt$('{0:D3}' -f $ValidationAttempt)"
)
$ExpectedManifestHash = "46bc9947bdaad189057b867c2a6cf6960c4694f5f5d908ea286c68d530cefc6a"
$Seeds = @(11, 29, 47)
$Heights = @(50, 75, 100)

if (Test-Path -LiteralPath $FreezePath) {
    throw "Methods are already frozen; validation selection may not be changed: $FreezePath"
}
if (-not (Test-Path -LiteralPath $Manifest -PathType Leaf)) {
    throw "Validation manifest is missing: $Manifest"
}
$ActualManifestHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $Manifest).Hash.ToLower()
if ($ActualManifestHash -ne $ExpectedManifestHash) {
    throw "Validation manifest hash mismatch: $ActualManifestHash != $ExpectedManifestHash"
}
$ProtocolPayload = Get-Content -LiteralPath $Protocol -Raw | ConvertFrom-Json
if (
    -not $ProtocolPayload.frozen_before_validation -or
    $ProtocolPayload.validation_manifest_sha256 -ne $ExpectedManifestHash -or
    $ProtocolPayload.runtime_version -ne $RuntimeVersion
) {
    throw "Frozen validation-selection protocol does not match this invocation"
}

$AllRuns = @()
$CompletedCandidates = @()
$ActiveRuns = @()
foreach ($Method in @("B", "C")) {
    $MethodFolder = if ($Method -eq "B") { "ppo_without_com" } else { "ppo_with_com" }
    $TrainingRoot = Join-Path $ProjectRoot "runs\$MethodFolder\training"
    $Pattern = "method-$Method-$RuntimeVersion`_seed-*_stage-*mm_attempt*"
    foreach ($RunDir in @(Get-ChildItem -LiteralPath $TrainingRoot -Directory -Filter $Pattern -ErrorAction SilentlyContinue)) {
        $ResultPath = Join-Path $RunDir.FullName "training_result.json"
        if (-not (Test-Path -LiteralPath $ResultPath -PathType Leaf)) {
            $AllRuns += [PSCustomObject]@{
                method = $Method
                run_name = $RunDir.Name
                run_dir = $RunDir.FullName
                status = "MISSING_TRAINING_RESULT"
                included_candidate = $false
            }
            continue
        }
        $Training = Get-Content -LiteralPath $ResultPath -Raw | ConvertFrom-Json
        $RunRecord = [PSCustomObject]@{
            method = $Method
            seed = [int]$Training.seed
            height_mm = [int]$Training.height_mm
            run_name = $RunDir.Name
            run_dir = $RunDir.FullName
            status = [string]$Training.status
            training_result = $ResultPath
            training_result_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $ResultPath).Hash.ToLower()
            included_candidate = $false
            checkpoint = $null
            checkpoint_sha256 = $null
        }
        if ($Training.status -eq "RUNNING") {
            $ActiveRuns += $RunRecord
        }
        if ($Training.status -eq "COMPLETED") {
            $Checkpoint = Join-Path $RunDir.FullName "checkpoints\final_agent.pt"
            if (-not (Test-Path -LiteralPath $Checkpoint -PathType Leaf)) {
                throw "COMPLETED training lacks final checkpoint: $RunDir"
            }
            $RecordedCheckpointHash = [string]$Training.final_checkpoint.sha256
            $ActualCheckpointHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $Checkpoint).Hash.ToLower()
            if ($RecordedCheckpointHash -ne $ActualCheckpointHash) {
                throw "Final checkpoint hash mismatch: $Checkpoint"
            }
            $RunRecord.included_candidate = $true
            $RunRecord.checkpoint = $Checkpoint
            $RunRecord.checkpoint_sha256 = $ActualCheckpointHash
            $CompletedCandidates += $RunRecord
        }
        $AllRuns += $RunRecord
    }
}
if ($ActiveRuns.Count -gt 0) {
    $Names = ($ActiveRuns | ForEach-Object { $_.run_name }) -join ", "
    throw "Training is still active; validation registry must wait: $Names"
}
foreach ($Method in @("B", "C")) {
    foreach ($Seed in $Seeds) {
        $CandidatesForSeed = @(
            $CompletedCandidates |
                Where-Object { $_.method -eq $Method -and $_.seed -eq $Seed }
        )
        foreach ($Height in $Heights) {
            if (@($CandidatesForSeed | Where-Object { $_.height_mm -eq $Height }).Count -lt 1) {
                throw "Incomplete formal training coverage: method=$Method seed=$Seed height=${Height}mm"
            }
        }
    }
}

New-Item -ItemType Directory -Path $ValidationRoot -Force | Out-Null
$RegistryPath = Join-Path $ValidationRoot "candidate_registry.json"
$Registry = [ordered]@{
    schema = "resume_validation.validation_candidate_registry.v1"
    runtime_version = $RuntimeVersion
    validation_attempt = $ValidationAttempt
    validation_manifest = $Manifest
    validation_manifest_sha256 = $ActualManifestHash
    selection_protocol = $Protocol
    selection_protocol_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $Protocol).Hash.ToLower()
    all_matching_runs = @($AllRuns | Sort-Object method, seed, height_mm, run_name)
    completed_candidates = @($CompletedCandidates | Sort-Object method, seed, height_mm, run_name)
}
$RegistryJson = $Registry | ConvertTo-Json -Depth 20
if (Test-Path -LiteralPath $RegistryPath) {
    $Existing = Get-Content -LiteralPath $RegistryPath -Raw
    if ($Existing.Trim() -ne $RegistryJson.Trim()) {
        throw "Candidate registry changed; preserve this campaign and use a new -ValidationAttempt"
    }
} else {
    $RegistryJson | Set-Content -LiteralPath $RegistryPath -Encoding UTF8
}

$PreviousPythonPath = $env:PYTHONPATH
$SourceRoot = Join-Path $ProjectRoot "src"
$env:PYTHONPATH = if ([string]::IsNullOrWhiteSpace($PreviousPythonPath)) {
    $SourceRoot
} else {
    "$SourceRoot$([IO.Path]::PathSeparator)$PreviousPythonPath"
}

function Invoke-Evaluation {
    param(
        [string]$Controller,
        [int]$Height,
        [string]$OutputDir,
        [string]$Checkpoint = ""
    )
    $ResultPath = Join-Path $OutputDir "result.json"
    if (Test-Path -LiteralPath $ResultPath -PathType Leaf) {
        $Existing = Get-Content -LiteralPath $ResultPath -Raw | ConvertFrom-Json
        if (-not $Existing.passed_execution) {
            throw "Preserved evaluation is failed; use a new -ValidationAttempt: $ResultPath"
        }
        return $ResultPath
    }
    if (Test-Path -LiteralPath $OutputDir) {
        throw "Incomplete evaluation directory exists; use a new -ValidationAttempt: $OutputDir"
    }
    $Arguments = @(
        "run", "--no-capture-output", "-n", "env_isaaclab",
        ".\isaaclab.bat", "-p", $Evaluator,
        "--controller", $Controller,
        "--manifest", $Manifest,
        "--height_mm", $Height,
        "--output_dir", $OutputDir,
        "--headless"
    )
    if (-not [string]::IsNullOrWhiteSpace($Checkpoint)) {
        $Arguments += @("--checkpoint", $Checkpoint)
    }
    # Stream simulator logs to the console without contaminating this
    # function's single returned result-path value.
    & conda @Arguments | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "Validation evaluation failed: controller=$Controller height=${Height}mm output=$OutputDir"
    }
    return $ResultPath
}

function Invoke-SelectionModule {
    param([string[]]$Arguments)
    & conda run --no-capture-output -n env_isaaclab python -m resume_validation.validation_selection @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Validation selection command failed: $($Arguments -join ' ')"
    }
}

Push-Location $IsaacLabRoot
try {
    $FsmDirectory = Join-Path $ValidationRoot "fsm"
    $FsmEvaluations = @()
    foreach ($Height in $Heights) {
        $Output = Join-Path $FsmDirectory "height-${Height}mm"
        $FsmEvaluations += Invoke-Evaluation -Controller "fsm" -Height $Height -OutputDir $Output
    }
    $FsmSummary = Join-Path $FsmDirectory "validation_summary.json"
    if (-not (Test-Path -LiteralPath $FsmSummary)) {
        Invoke-SelectionModule -Arguments @(
            "summarize",
            "--controller", "fsm",
            "--validation_manifest", $Manifest,
            "--evaluations", $FsmEvaluations[0], $FsmEvaluations[1], $FsmEvaluations[2],
            "--output", $FsmSummary
        )
    }

    foreach ($Method in @("B", "C")) {
        foreach ($Seed in $Seeds) {
            $CandidateSummaries = @()
            $CandidatesForSeed = @(
                $CompletedCandidates |
                    Where-Object { $_.method -eq $Method -and $_.seed -eq $Seed } |
                    Sort-Object height_mm, run_name
            )
            foreach ($Candidate in $CandidatesForSeed) {
                $CandidateDirectory = Join-Path $ValidationRoot (
                    "method-$Method\seed-$Seed\candidates\$($Candidate.run_name)"
                )
                $EvaluationPaths = @()
                foreach ($Height in $Heights) {
                    $Output = Join-Path $CandidateDirectory "height-${Height}mm"
                    $EvaluationPaths += Invoke-Evaluation `
                        -Controller $Method `
                        -Height $Height `
                        -OutputDir $Output `
                        -Checkpoint $Candidate.checkpoint
                }
                $SummaryPath = Join-Path $CandidateDirectory "validation_summary.json"
                if (-not (Test-Path -LiteralPath $SummaryPath)) {
                    Invoke-SelectionModule -Arguments @(
                        "summarize",
                        "--controller", $Method,
                        "--seed", [string]$Seed,
                        "--checkpoint", $Candidate.checkpoint,
                        "--validation_manifest", $Manifest,
                        "--evaluations", $EvaluationPaths[0], $EvaluationPaths[1], $EvaluationPaths[2],
                        "--output", $SummaryPath
                    )
                }
                $CandidateSummaries += $SummaryPath
            }
            $SelectionDirectory = Join-Path $ValidationRoot "method-$Method\seed-$Seed"
            New-Item -ItemType Directory -Path $SelectionDirectory -Force | Out-Null
            $SelectionPath = Join-Path $SelectionDirectory "checkpoint_selection.json"
            if (-not (Test-Path -LiteralPath $SelectionPath)) {
                $SelectionArguments = @(
                    "select",
                    "--method", $Method,
                    "--seed", [string]$Seed,
                    "--fsm_summary", $FsmSummary,
                    "--candidate_summaries"
                ) + $CandidateSummaries + @("--output", $SelectionPath)
                Invoke-SelectionModule -Arguments $SelectionArguments
            }
        }
    }
} finally {
    Pop-Location
    $env:PYTHONPATH = $PreviousPythonPath
}

Write-Output "Validation campaign complete: $ValidationRoot"
