param(
    [string]$RuntimeVersion = "v34",
    [int]$LockedAttempt = 1,
    [ValidateRange(1, 120)]
    [int]$RecordStride = 10
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$IsaacLabRoot = "C:\robotics_sim\IsaacLab"
$Evaluator = Join-Path $ProjectRoot "src\resume_validation\evaluate_controller.py"
$FreezePath = Join-Path $ProjectRoot "configs\method_freeze.json"
if (-not (Test-Path -LiteralPath $FreezePath -PathType Leaf)) {
    throw "Method freeze is absent; locked-test access is forbidden"
}
$FreezeHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $FreezePath).Hash.ToLower()
$RunRoot = Join-Path $ProjectRoot (
    "runs\locked_test\runtime-$RuntimeVersion`_freeze-$($FreezeHash.Substring(0,12))" +
    "_attempt$('{0:D3}' -f $LockedAttempt)"
)
New-Item -ItemType Directory -Path $RunRoot -Force | Out-Null
$AuthorizationPath = Join-Path $RunRoot "locked_test_authorization.json"
$AuditPath = Join-Path $RunRoot "paired_coverage_audit.json"
$PreviousPythonPath = $env:PYTHONPATH
$SourceRoot = Join-Path $ProjectRoot "src"
$env:PYTHONPATH = if ([string]::IsNullOrWhiteSpace($PreviousPythonPath)) {
    $SourceRoot
} else {
    "$SourceRoot$([IO.Path]::PathSeparator)$PreviousPythonPath"
}

try {
    & "C:\Users\kskzz\miniconda3\envs\env_isaaclab\python.exe" `
        -m resume_validation.method_freeze verify `
        --freeze $FreezePath
    if ($LASTEXITCODE -ne 0) {
        throw "Method freeze verification failed; locked-test access remains forbidden"
    }
    if (-not (Test-Path -LiteralPath $AuthorizationPath)) {
        & "C:\Users\kskzz\miniconda3\envs\env_isaaclab\python.exe" `
            -m resume_validation.locked_test_guard authorize `
            --freeze $FreezePath `
            --project_root $ProjectRoot `
            --output $AuthorizationPath
        if ($LASTEXITCODE -ne 0) {
            throw "Locked-test authorization failed before manifest access"
        }
    }
    $Authorization = Get-Content -LiteralPath $AuthorizationPath -Raw | ConvertFrom-Json
    if (
        -not $Authorization.method_freeze_verified -or
        $Authorization.method_freeze_sha256 -ne $FreezeHash -or
        -not $Authorization.locked_manifest_sidecar_verified
    ) {
        throw "Existing locked-test authorization is invalid"
    }
    $Manifest = [string]$Authorization.locked_manifest
    $ManifestHash = [string]$Authorization.locked_manifest_sha256
    $Freeze = Get-Content -LiteralPath $FreezePath -Raw | ConvertFrom-Json
    if ($Freeze.runtime_version -ne $RuntimeVersion) {
        throw "Runtime version does not match the method freeze"
    }

    function Invoke-LockedEvaluation {
        param(
            [string]$Controller,
            [int]$Height,
            [string]$OutputDir,
            [string]$Checkpoint = "",
            [string]$CheckpointHash = ""
        )
        $ResultPath = Join-Path $OutputDir "result.json"
        if (Test-Path -LiteralPath $ResultPath -PathType Leaf) {
            $Result = Get-Content -LiteralPath $ResultPath -Raw | ConvertFrom-Json
            $ActualCheckpointHash = if ([string]::IsNullOrWhiteSpace($CheckpointHash)) {
                $null
            } else {
                $CheckpointHash
            }
            if (
                -not $Result.passed_execution -or
                $Result.controller -ne $Controller -or
                [int]$Result.height_mm -ne $Height -or
                [int]$Result.aggregate.episode_count -ne 100 -or
                $Result.provenance.manifest_sha256 -ne $ManifestHash -or
                $Result.provenance.checkpoint_sha256 -ne $ActualCheckpointHash
            ) {
                throw "Preserved locked evaluation is invalid; use a new -LockedAttempt: $ResultPath"
            }
            return
        }
        if (Test-Path -LiteralPath $OutputDir) {
            throw "Incomplete locked evaluation exists; use a new -LockedAttempt: $OutputDir"
        }
        $Arguments = @(
            "run", "--no-capture-output", "-n", "env_isaaclab",
            ".\isaaclab.bat", "-p", $Evaluator,
            "--controller", $Controller,
            "--manifest", $Manifest,
            "--require_locked_hash", $ManifestHash,
            "--height_mm", $Height,
            "--output_dir", $OutputDir,
            "--record_stride", $RecordStride,
            "--headless"
        )
        if (-not [string]::IsNullOrWhiteSpace($Checkpoint)) {
            $Arguments += @("--checkpoint", $Checkpoint)
        }
        & conda @Arguments | Out-Host
        if ($LASTEXITCODE -ne 0) {
            throw "Locked evaluation failed: controller=$Controller height=${Height}mm"
        }
    }

    Push-Location $IsaacLabRoot
    try {
        foreach ($Height in @(50, 75, 100)) {
            Invoke-LockedEvaluation `
                -Controller "fsm" `
                -Height $Height `
                -OutputDir (Join-Path $RunRoot "fsm\height-${Height}mm")
        }
        foreach ($Method in @("B", "C")) {
            foreach ($Seed in @(11, 29, 47)) {
                $Selection = @(
                    $Freeze.selections |
                        Where-Object { $_.method -eq $Method -and [int]$_.seed -eq $Seed }
                )
                if ($Selection.Count -ne 1) {
                    throw "Method freeze selection missing or duplicated: method=$Method seed=$Seed"
                }
                foreach ($Height in @(50, 75, 100)) {
                    Invoke-LockedEvaluation `
                        -Controller $Method `
                        -Height $Height `
                        -Checkpoint $Selection[0].selected_checkpoint `
                        -CheckpointHash $Selection[0].selected_checkpoint_sha256 `
                        -OutputDir (
                            Join-Path $RunRoot "method-$Method\seed-$Seed\height-${Height}mm"
                        )
                }
            }
        }
    } finally {
        Pop-Location
    }

    if (-not (Test-Path -LiteralPath $AuditPath)) {
        & "C:\Users\kskzz\miniconda3\envs\env_isaaclab\python.exe" `
            -m resume_validation.locked_test_guard audit `
            --freeze $FreezePath `
            --authorization $AuthorizationPath `
            --run_root $RunRoot `
            --output $AuditPath
        if ($LASTEXITCODE -ne 0) {
            throw "Locked-test paired coverage audit failed"
        }
    }
} finally {
    $env:PYTHONPATH = $PreviousPythonPath
}

Write-Output "Locked paired test complete: $RunRoot"
