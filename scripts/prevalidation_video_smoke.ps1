[CmdletBinding()]
param(
    [int]$Attempt = 1
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$IsaacLabRoot = "C:\robotics_sim\IsaacLab"
$Evaluator = Join-Path $ProjectRoot "src\resume_validation\evaluate_controller.py"
$Manifest = Join-Path $ProjectRoot "data\scenario_manifests\development_v2.json"
$ExpectedManifestHash = "f3d10d7340c06f78c200c44119bb2e17c81e587bd314b342ac90b49019ea2cdc"
$ScenarioId = "development-h050-0000"
$OutputDir = Join-Path $ProjectRoot (
    "runs\diagnostics\prevalidation_video_smoke_attempt$('{0:D3}' -f $Attempt)"
)
$ResultPath = Join-Path $OutputDir "result.json"
$VideoPath = Join-Path $OutputDir "replay.mp4"
$VideoProbePath = Join-Path $OutputDir "video_probe.json"
$Python = "C:\Users\kskzz\miniconda3\envs\env_isaaclab\python.exe"

if (-not (Test-Path -LiteralPath $Manifest -PathType Leaf)) {
    throw "Development manifest is missing: $Manifest"
}
$ManifestHash = (
    Get-FileHash -LiteralPath $Manifest -Algorithm SHA256
).Hash.ToLowerInvariant()
if ($ManifestHash -ne $ExpectedManifestHash) {
    throw "Development manifest hash mismatch: $ManifestHash"
}

function Assert-VideoSmokeResult {
    if (-not (Test-Path -LiteralPath $ResultPath -PathType Leaf)) {
        throw "Video smoke produced no result: $ResultPath"
    }
    $Result = Get-Content -LiteralPath $ResultPath -Raw | ConvertFrom-Json
    if (
        -not [bool]$Result.passed_execution -or
        $Result.controller -ne "fsm" -or
        [int]$Result.height_mm -ne 50 -or
        $Result.provenance.manifest_sha256 -ne $ExpectedManifestHash -or
        $Result.video_replay.scenario_id -ne $ScenarioId -or
        [int]$Result.video_replay.frame_count -lt 1 -or
        -not (Test-Path -LiteralPath $VideoPath -PathType Leaf)
    ) {
        throw "Video smoke result/provenance is invalid: $ResultPath"
    }
    $VideoHash = (
        Get-FileHash -LiteralPath $VideoPath -Algorithm SHA256
    ).Hash.ToLowerInvariant()
    if (
        $VideoHash -ne [string]$Result.artifacts.video_sha256 -or
        (Get-Item -LiteralPath $VideoPath).Length -le 0
    ) {
        throw "Video smoke encoding/hash is invalid: $VideoPath"
    }
    if (-not (Test-Path -LiteralPath $VideoProbePath -PathType Leaf)) {
        throw "Video smoke decode probe is missing: $VideoProbePath"
    }
    $Probe = Get-Content -LiteralPath $VideoProbePath -Raw | ConvertFrom-Json
    if (
        -not [bool]$Probe.decoded -or
        [int]$Probe.width -ne 960 -or
        [int]$Probe.height -ne 540 -or
        [math]::Abs([double]$Probe.fps - 20.0) -gt 0.05 -or
        [int]$Probe.decoded_frame_count -ne
        [int]$Result.video_replay.frame_count -or
        [string]$Probe.video_sha256 -ne $VideoHash
    ) {
        throw "Video smoke decode probe is invalid: $VideoProbePath"
    }
    $Episodes = [string]$Result.artifacts.episodes
    if (
        -not (Test-Path -LiteralPath $Episodes -PathType Leaf) -or
        (Get-FileHash -LiteralPath $Episodes -Algorithm SHA256).Hash.ToLowerInvariant() -ne
        [string]$Result.artifacts.episodes_sha256
    ) {
        throw "Video smoke episode artifact is invalid: $Episodes"
    }
    $Rows = @(Get-Content -LiteralPath $Episodes | ForEach-Object {
        $_ | ConvertFrom-Json
    })
    if (
        $Rows.Count -ne 1 -or
        $Rows[0].scenario_id -ne $ScenarioId -or
        -not [bool]$Rows[0].success
    ) {
        throw "Video smoke did not reproduce the registered development success"
    }
    Write-Output "Prevalidation physical video smoke passed: $ResultPath"
}

if (Test-Path -LiteralPath $ResultPath -PathType Leaf) {
    Assert-VideoSmokeResult
    return
}
if (Test-Path -LiteralPath $OutputDir) {
    throw "Incomplete video smoke exists; preserve it and increment -Attempt: $OutputDir"
}

Push-Location $IsaacLabRoot
try {
    & conda run --no-capture-output -n env_isaaclab .\isaaclab.bat -p $Evaluator `
        --controller fsm `
        --manifest $Manifest `
        --height_mm 50 `
        --scenario_id $ScenarioId `
        --output_dir $OutputDir `
        --record_stride 3 `
        --video_path $VideoPath `
        --video_stride 3 `
        --video_fps 20 `
        --video_category "prevalidation_physical_render_smoke" `
        --video_outcome_label "success" `
        --enable_cameras `
        --headless
    if ($LASTEXITCODE -ne 0) {
        throw "Prevalidation physical video smoke failed"
    }
} finally {
    Pop-Location
}

$ProbeCode = @'
import hashlib
import json
import sys
from pathlib import Path

import imageio.v2 as imageio

video = Path(sys.argv[1]).resolve()
output = Path(sys.argv[2]).resolve()
reader = imageio.get_reader(video)
try:
    metadata = reader.get_meta_data()
    first = reader.get_data(0)
    decoded_frame_count = int(reader.count_frames())
finally:
    reader.close()
height, width = (int(first.shape[0]), int(first.shape[1]))
payload = {
    "schema": "resume_validation.video_decode_probe.v1",
    "decoded": True,
    "video": str(video),
    "video_sha256": hashlib.sha256(video.read_bytes()).hexdigest(),
    "width": width,
    "height": height,
    "fps": float(metadata["fps"]),
    "codec": str(metadata.get("codec", "")),
    "decoded_frame_count": decoded_frame_count,
}
output.write_text(
    json.dumps(payload, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
'@
& $Python -c $ProbeCode $VideoPath $VideoProbePath
if ($LASTEXITCODE -ne 0) {
    throw "Video smoke MP4 decode probe failed"
}

Assert-VideoSmokeResult
