[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateRange(1, [int]::MaxValue)]
    [int]$SupervisorPid,
    [ValidateRange(1, 999)]
    [int]$Attempt = 1,
    [ValidateRange(10, 60)]
    [int]$PollSeconds = 30
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$OrchestrationRoot = Join-Path $ProjectRoot "runs\orchestration"
$StatusPath = Join-Path $OrchestrationRoot (
    "full_pipeline_keep_awake_attempt$('{0:D3}' -f $Attempt).json"
)

Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;

public static class PipelineExecutionState
{
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern uint SetThreadExecutionState(uint esFlags);
}
"@

$EsContinuous = [uint32]2147483648
$EsSystemRequired = [uint32]0x00000001

function Write-KeepAwakeStatus {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Status,
        [Parameter(Mandatory = $true)]
        [string]$Message,
        [uint32]$NativeReturn = 0
    )
    $Payload = [ordered]@{
        schema = "resume_validation.pipeline_keep_awake.v1"
        updated_utc = (Get-Date).ToUniversalTime().ToString("o")
        helper_pid = $PID
        supervisor_pid = $SupervisorPid
        attempt = $Attempt
        status = $Status
        message = $Message
        requested_execution_state = "ES_CONTINUOUS | ES_SYSTEM_REQUIRED"
        native_return = $NativeReturn
        power_plan_modified = $false
        administrator_privileges_required = $false
    }
    New-Item -ItemType Directory -Path $OrchestrationRoot -Force | Out-Null
    $Temporary = Join-Path $OrchestrationRoot (
        ".{0}.{1}.tmp" -f
        (Split-Path -Leaf $StatusPath),
        ([Guid]::NewGuid().ToString("N"))
    )
    $Payload | ConvertTo-Json -Depth 10 |
        Set-Content -LiteralPath $Temporary -Encoding UTF8
    Move-Item -LiteralPath $Temporary -Destination $StatusPath -Force
}

if (Test-Path -LiteralPath $StatusPath -PathType Leaf) {
    throw "Keep-awake attempt evidence already exists; increment -Attempt: $StatusPath"
}

$LastReturn = [uint32]0
try {
    while ($null -ne (
        Get-Process -Id $SupervisorPid -ErrorAction SilentlyContinue
    )) {
        $LastReturn = [PipelineExecutionState]::SetThreadExecutionState(
            $EsContinuous -bor $EsSystemRequired
        )
        if ($LastReturn -eq 0) {
            $Win32Error = [Runtime.InteropServices.Marshal]::GetLastWin32Error()
            throw "SetThreadExecutionState failed with Win32 error $Win32Error"
        }
        Write-KeepAwakeStatus `
            -Status "ACTIVE" `
            -Message "System idle sleep is suppressed while the recorded full-pipeline supervisor remains alive." `
            -NativeReturn $LastReturn
        Start-Sleep -Seconds $PollSeconds
    }
    Write-KeepAwakeStatus `
        -Status "SUPERVISOR_EXITED" `
        -Message "The recorded full-pipeline supervisor exited; releasing the execution-state request." `
        -NativeReturn $LastReturn
} catch {
    Write-KeepAwakeStatus `
        -Status "FAILED" `
        -Message $_.Exception.Message `
        -NativeReturn $LastReturn
    exit 1
} finally {
    [void][PipelineExecutionState]::SetThreadExecutionState($EsContinuous)
}

Write-KeepAwakeStatus `
    -Status "COMPLETED" `
    -Message "Execution-state request released after the full-pipeline supervisor exited." `
    -NativeReturn $LastReturn
