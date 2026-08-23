param(
    [Parameter(Mandatory = $true)]
    [int]$ProcessId,
    [Parameter(Mandatory = $true)]
    [string]$ProgressFile,
    [int]$NoProgressMinutes = 20,
    [int]$PollSeconds = 30
)
$ErrorActionPreference = "Stop"
$ResolvedProgress = [System.IO.Path]::GetFullPath($ProgressFile)
$LastLength = -1L
$LastWrite = [datetime]::MinValue
$LastProgress = Get-Date

while ($true) {
    $Process = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if ($null -eq $Process) { exit 0 }
    if (Test-Path -LiteralPath $ResolvedProgress) {
        $File = Get-Item -LiteralPath $ResolvedProgress
        if (($File.Length -ne $LastLength) -or ($File.LastWriteTimeUtc -ne $LastWrite)) {
            $LastLength = $File.Length
            $LastWrite = $File.LastWriteTimeUtc
            $LastProgress = Get-Date
        }
    }
    if (((Get-Date) - $LastProgress).TotalMinutes -ge $NoProgressMinutes) {
        Stop-Process -Id $ProcessId -Force
        throw "Watchdog terminated process $ProcessId after $NoProgressMinutes minutes without progress in $ResolvedProgress"
    }
    Start-Sleep -Seconds ([Math]::Min(60, [Math]::Max(5, $PollSeconds)))
}
