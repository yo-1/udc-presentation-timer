param(
    [Parameter(Mandatory=$true)][string]$Payload,
    [Parameter(Mandatory=$true)][string]$Evidence
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$Payload = (Resolve-Path -LiteralPath $Payload).Path
$Evidence = (Resolve-Path -LiteralPath $Evidence).Path
$Report = @{ schema=1; status='not_run'; payload=$Payload; candidate_executed=$false }
function Save-Report {
    $Report | ConvertTo-Json -Depth 8 | Set-Content -Encoding utf8 (Join-Path $Evidence 'defender-scan.json')
    Write-Output "Defender scan status: $($Report.status). This is not a safety verdict."
}
try {
    $Status = Get-MpComputerStatus
    $Report.engine = $Status.AMEngineVersion
    $Report.product = $Status.AMProductVersion
    $Report.signature = $Status.AntivirusSignatureVersion
    $Report.running_mode = $Status.AMRunningMode
    $Report.antivirus_enabled = $Status.AntivirusEnabled
    $Report.real_time_enabled = $Status.RealTimeProtectionEnabled
} catch {
    $Report.reason = "Defender status unavailable: $($_.Exception.Message)"
    Save-Report
    return
}
if (-not $Status.AntivirusEnabled -or $Status.AMRunningMode -ne 'Normal') {
    $Report.reason = 'Defender is not active in Normal mode. No settings were changed.'
    Save-Report
    return
}
$Candidates = @(Get-ChildItem "$env:ProgramData/Microsoft/Windows Defender/Platform/*/MpCmdRun.exe" -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending)
$Fallback = Join-Path $env:ProgramFiles 'Windows Defender/MpCmdRun.exe'
if ($Candidates.Count -gt 0) { $Scanner = $Candidates[0].FullName }
elseif (Test-Path -LiteralPath $Fallback) { $Scanner = $Fallback }
else {
    $Report.reason = 'MpCmdRun executable unavailable.'
    Save-Report
    return
}
try {
    Update-MpSignature
    $Status = Get-MpComputerStatus
    $Report.signature = $Status.AntivirusSignatureVersion
    $Report.signature_updated = $Status.AntivirusSignatureLastUpdated.ToUniversalTime().ToString('o')
    $Started = Get-Date
    $Report.started_utc = $Started.ToUniversalTime().ToString('o')
    $Report.status = 'running'
    Save-Report
    # Native invocation waits for completion. No payload execution, exclusions,
    # disabled remediation, scan cancellation or protection changes are used.
    & $Scanner -Scan -ScanType 3 -File $Payload
    $Report.scanner_exit_code = $LASTEXITCODE
    $Report.finished_utc = (Get-Date).ToUniversalTime().ToString('o')
    $Report.detections = @(Get-MpThreatDetection | Where-Object {
        $_.InitialDetectionTime -ge $Started.AddSeconds(-1) -and
        @($_.Resources | Where-Object {
            $_.IndexOf($Payload, [StringComparison]::OrdinalIgnoreCase) -ge 0
        }).Count -gt 0
    } | Select-Object ThreatID, InitialDetectionTime, ActionSuccess, Resources)
    if ($Report.scanner_exit_code -ne 0 -or $Report.detections.Count -gt 0) {
        $Report.status = 'detection_or_error'
        Save-Report
        throw 'Defender detected a threat or scanning did not complete successfully. Preserve quarantine and inspect the report.'
    }
    # Exit 0 can ALSO mean malware was remediated. Record the evidence precisely;
    # it must not be described as a guarantee that the candidate is safe.
    $Report.status = 'completed_exit_0_no_matching_detection_record'
    Save-Report
} catch {
    if ($Report.status -ne 'detection_or_error') {
        $Report.status = 'failed_or_unknown'
        $Report.reason = $_.Exception.Message
        Save-Report
    }
    throw
}
