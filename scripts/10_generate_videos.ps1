param(
    [string]$RuntimeVersion = "v34",
    [int]$LockedAttempt = 1,
    [int]$VideoAttempt = 1
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$IsaacLabRoot = "C:\robotics_sim\IsaacLab"
$Evaluator = Join-Path $ProjectRoot "src\resume_validation\evaluate_controller.py"
$FreezePath = Join-Path $ProjectRoot "configs\method_freeze.json"
if (-not (Test-Path -LiteralPath $FreezePath -PathType Leaf)) {
    throw "Method freeze is missing"
}
$FreezeHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $FreezePath).Hash.ToLower()
$LockedRoot = Join-Path $ProjectRoot (
    "runs\locked_test\runtime-$RuntimeVersion`_freeze-$($FreezeHash.Substring(0,12))" +
    "_attempt$('{0:D3}' -f $LockedAttempt)"
)
$Authorization = Join-Path $LockedRoot "locked_test_authorization.json"
$Audit = Join-Path $LockedRoot "paired_coverage_audit.json"
if (
    -not (Test-Path -LiteralPath $Authorization -PathType Leaf) -or
    -not (Test-Path -LiteralPath $Audit -PathType Leaf)
) {
    throw "Locked paired campaign is incomplete: $LockedRoot"
}
$VideosRoot = Join-Path $ProjectRoot (
    "reports\videos\runtime-$RuntimeVersion`_freeze-$($FreezeHash.Substring(0,12))" +
    "_locked$('{0:D3}' -f $LockedAttempt)_video$('{0:D3}' -f $VideoAttempt)"
)
New-Item -ItemType Directory -Path $VideosRoot -Force | Out-Null
$SelectionPath = Join-Path $VideosRoot "video_selection.json"
$InventoryPath = Join-Path $VideosRoot "video_inventory.json"
$Python = "C:\Users\kskzz\miniconda3\envs\env_isaaclab\python.exe"
$PreviousPythonPath = $env:PYTHONPATH
$SourceRoot = Join-Path $ProjectRoot "src"
$env:PYTHONPATH = if ([string]::IsNullOrWhiteSpace($PreviousPythonPath)) {
    $SourceRoot
} else {
    "$SourceRoot$([IO.Path]::PathSeparator)$PreviousPythonPath"
}

try {
    & $Python -m resume_validation.method_freeze verify --freeze $FreezePath
    if ($LASTEXITCODE -ne 0) {
        throw "Method freeze drift; video replays are unauthorized"
    }
    if (-not (Test-Path -LiteralPath $SelectionPath)) {
        & $Python -m resume_validation.video_selection select `
            --project_root $ProjectRoot `
            --freeze $FreezePath `
            --authorization $Authorization `
            --locked_run_root $LockedRoot `
            --audit $Audit `
            --output $SelectionPath
        if ($LASTEXITCODE -ne 0) {
            throw "Deterministic video episode selection failed"
        }
    }
    $Selection = Get-Content -LiteralPath $SelectionPath -Raw | ConvertFrom-Json
    if (
        $Selection.method_freeze_sha256 -ne $FreezeHash -or
        [int]$Selection.locked_episode_count_considered -ne 2100
    ) {
        throw "Existing video selection does not match the frozen locked campaign"
    }

    Push-Location $IsaacLabRoot
    try {
        for ($Index = 0; $Index -lt $Selection.selections.Count; $Index++) {
            $Selected = $Selection.selections[$Index]
            $OutputDir = Join-Path $VideosRoot "replay-$('{0:D3}' -f $Index)"
            $ResultPath = Join-Path $OutputDir "result.json"
            if (Test-Path -LiteralPath $ResultPath -PathType Leaf) {
                $Existing = Get-Content -LiteralPath $ResultPath -Raw | ConvertFrom-Json
                if (
                    -not $Existing.passed_execution -or
                    $Existing.controller -ne $Selected.method -or
                    [int]$Existing.height_mm -ne [int]$Selected.height_mm -or
                    $Existing.provenance.checkpoint_sha256 -ne $Selected.checkpoint_sha256 -or
                    -not (Test-Path -LiteralPath $Existing.artifacts.video -PathType Leaf)
                ) {
                    throw "Existing video replay is invalid; use a new -VideoAttempt: $ResultPath"
                }
                continue
            }
            if (Test-Path -LiteralPath $OutputDir) {
                throw "Incomplete video replay exists; use a new -VideoAttempt: $OutputDir"
            }
            $VideoPath = Join-Path $OutputDir "replay.mp4"
            $Outcome = if ($Selected.locked_success) { "success" } else { "failure" }
            $Categories = @($Selected.categories) -join "+"
            $Arguments = @(
                "run", "--no-capture-output", "-n", "env_isaaclab",
                ".\isaaclab.bat", "-p", $Evaluator,
                "--controller", [string]$Selected.method,
                "--manifest", [string]$Selection.locked_manifest,
                "--require_locked_hash", [string]$Selection.locked_manifest_sha256,
                "--height_mm", [string]$Selected.height_mm,
                "--scenario_id", [string]$Selected.scenario_id,
                "--output_dir", $OutputDir,
                "--record_stride", "10",
                "--video_path", $VideoPath,
                "--video_stride", "3",
                "--video_fps", "20",
                "--video_category", $Categories,
                "--video_outcome_label", $Outcome,
                "--enable_cameras",
                "--headless"
            )
            if ($null -ne $Selected.checkpoint) {
                $Arguments += @("--checkpoint", [string]$Selected.checkpoint)
            }
            & conda @Arguments | Out-Host
            if ($LASTEXITCODE -ne 0) {
                throw (
                    "Video replay failed: method=$($Selected.method) " +
                    "height=$($Selected.height_mm) scenario=$($Selected.scenario_id)"
                )
            }
        }
    } finally {
        Pop-Location
    }

    if (-not (Test-Path -LiteralPath $InventoryPath)) {
        & $Python -m resume_validation.video_selection inventory `
            --selection $SelectionPath `
            --videos_root $VideosRoot `
            --output $InventoryPath
        if ($LASTEXITCODE -ne 0) {
            throw "Video inventory/provenance audit failed"
        }
    }
} finally {
    $env:PYTHONPATH = $PreviousPythonPath
}

Write-Output "Video evidence complete: $InventoryPath"
