[CmdletBinding()]
param()

. (Join-Path $PSScriptRoot 'inspection_common.ps1')

$fsm = Join-Path $script:ProjectRoot 'configs\fsm.yaml'
[pscustomobject]@{ Controller='FSM'; Seed=''; HeightMm='50/75/100'; Attempt='frozen'; Status='AVAILABLE'; Role='frozen config'; Path=$fsm; SHA256=Get-Sha256Lower $fsm; GateRate='development 12/20, 7/20, 7/20'; Promote='N/A' } | Format-List

$controllerRows = foreach ($method in @('B','C')) {
    $folder = if ($method -eq 'B') { 'ppo_without_com' } else { 'ppo_with_com' }
    $root = Join-Path $script:ProjectRoot "runs\$folder\training"
    Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue | Where-Object Name -Match "^method-$method-v34_seed-(\d+)_stage-(50|75|100)mm_attempt(\d+)$" | ForEach-Object {
        $seed = [int]$Matches[1]; $height = [int]$Matches[2]; $attempt = [int]$Matches[3]
        $resultPath = Join-Path $_.FullName 'training_result.json'
        $result = if (Test-Path -LiteralPath $resultPath) { Get-Content -LiteralPath $resultPath -Raw | ConvertFrom-Json } else { $null }
        $gateDir = Join-Path $script:ProjectRoot "runs\$folder\development_gates\$($_.Name)"
        $gatePath = Join-Path $gateDir 'gate_decision.json'
        $evalPath = Join-Path $gateDir 'result.json'
        $gate = if (Test-Path -LiteralPath $gatePath) { Get-Content -LiteralPath $gatePath -Raw | ConvertFrom-Json } else { $null }
        $evaluation = if (Test-Path -LiteralPath $evalPath) { Get-Content -LiteralPath $evalPath -Raw | ConvertFrom-Json } else { $null }
        foreach ($checkpoint in @(Get-ChildItem -LiteralPath (Join-Path $_.FullName 'checkpoints') -Filter '*.pt' -File -ErrorAction SilentlyContinue | Where-Object Name -In @('best_agent.pt','final_agent.pt') | Sort-Object Name)) {
            $role = if ($checkpoint.Name -eq 'best_agent.pt') { 'best' } elseif ($checkpoint.Name -eq 'final_agent.pt') { 'final' } else { 'intermediate' }
            [pscustomobject]@{
                Controller=$method; Seed=$seed; HeightMm=$height; Attempt=$attempt; Status=if($result){$result.status}else{'UNKNOWN'}
                Role=$role; Path=$checkpoint.FullName; SHA256=Get-Sha256Lower $checkpoint.FullName
                GateRate=if($evaluation){$evaluation.aggregate.success_rate}else{''}; Promote=if($gate){$gate.promote}else{''}
            }
        }
    }
}
$controllerRows | Format-Table -Wrap -AutoSize

Write-Host 'Note: best_agent means highest tracked training return, not development success. RUNNING Method C checkpoints are incomplete and are not auto-selectable.'
