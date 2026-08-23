[CmdletBinding()]
param()

. (Join-Path $PSScriptRoot 'inspection_common.ps1')

$safety = Get-InspectionSafety
$supervisor = Get-ChildItem -LiteralPath (Join-Path $script:ProjectRoot 'runs\orchestration') -Filter 'full_pipeline_supervisor_attempt*.json' -File -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime | Select-Object -Last 1
$supervisorState = if ($supervisor) { Get-Content -LiteralPath $supervisor.FullName -Raw | ConvertFrom-Json } else { $null }
$trainingResults = @(Get-ChildItem -LiteralPath (Join-Path $script:ProjectRoot 'runs') -Recurse -Filter 'training_result.json' -File |
    Where-Object FullName -NotMatch 'chatgpt_handoff_' | ForEach-Object {
        try { Get-Content -LiteralPath $_.FullName -Raw | ConvertFrom-Json } catch { $null }
    } | Where-Object { $_ })
$completed = @($trainingResults | Where-Object status -EQ 'COMPLETED' | Group-Object method,seed,height_mm | ForEach-Object { $_.Group | Select-Object -Last 1 })
$runningRecords = @($trainingResults | Where-Object status -EQ 'RUNNING')
$running = @($runningRecords | Where-Object {
    $recordedPid = [int]$_.provenance.pid
    $recordedPid -gt 0 -and (Get-Process -Id $recordedPid -ErrorAction SilentlyContinue)
})
$staleRunning = @($runningRecords | Where-Object {
    $recordedPid = [int]$_.provenance.pid
    $recordedPid -le 0 -or -not (Get-Process -Id $recordedPid -ErrorAction SilentlyContinue)
})
$gates = @(Get-ChildItem -LiteralPath (Join-Path $script:ProjectRoot 'runs') -Recurse -Filter 'gate_decision.json' -File | ForEach-Object {
    try { Get-Content -LiteralPath $_.FullName -Raw | ConvertFrom-Json } catch { $null }
} | Where-Object { $_ })

Write-Host "Project: $script:ProjectRoot"
Write-Host "Audit time: $((Get-Date).ToUniversalTime().ToString('o'))"
Write-Host "GUI/diagnostic launch safe: $($safety.Safe) — $($safety.Reason)"
if ($supervisorState) { Write-Host "Latest supervisor: attempt=$($supervisorState.attempt) status=$($supervisorState.status) updated=$($supervisorState.updated_utc)" }
Write-Host "Completed formal training strata: $($completed.Count); development gates: $($gates.Count)"
if ($running.Count) {
    Write-Host 'Live training records (recorded PID still exists):'
    $running | Select-Object method,seed,height_mm,status,started_unix,run_dir | Format-Table -AutoSize
}
if ($staleRunning.Count) { Write-Host "Stale RUNNING metadata records with no live recorded PID: $($staleRunning.Count) (not counted as active training)." }
if ($safety.Blockers.Count) {
    Write-Host 'Active blockers (read-only; never terminate them from inspection scripts):'
    $safety.Blockers | Select-Object PID,ParentPID,Name,CreationUtc,CPUSeconds,WorkingSetBytes,Responding,CommandLine | Format-Table -Wrap -AutoSize
}
Write-Host "Method C artifacts: $(@(Get-ChildItem -LiteralPath (Join-Path $script:ProjectRoot 'runs\ppo_with_com') -Recurse -File -ErrorAction SilentlyContinue).Count) files"
Write-Host "Method freeze exists: $(Test-Path -LiteralPath (Join-Path $script:ProjectRoot 'configs\method_freeze.json'))"
Write-Host "Locked-test result directory exists: $(Test-Path -LiteralPath (Join-Path $script:ProjectRoot 'runs\locked_test'))"
