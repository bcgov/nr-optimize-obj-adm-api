# Monitor-GDsvc.ps1
# Checks the GDsvc Windows service and starts it if stopped.
# Logs to E:\LogFiles\GeoDrive\Monitoring\GDsvc-monitor.log
# Writes Event Log entries when it intervenes.

$ServiceName  = "GDsvc"
$LogFolder    = "E:\LogFiles\GeoDrive\Monitoring"
$LogPath      = Join-Path $LogFolder "GDsvc-monitor.log"
$EventSource  = "GDsvc-Monitor"
$EventLogName = "Application"

if (-not (Test-Path -LiteralPath $LogFolder)) {
    New-Item -Path $LogFolder -ItemType Directory -Force | Out-Null
}

try {
    if (-not [System.Diagnostics.EventLog]::SourceExists($EventSource)) {
        New-EventLog -LogName $EventLogName -Source $EventSource
    }
} catch {
    # Continue even if event source cannot be created on first run
}

function Write-Log {
    param([string]$Message)
    $ts = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    Add-Content -LiteralPath $LogPath -Value ("{0}`t{1}" -f $ts, $Message)
}

try {
    $svc = Get-Service -Name $ServiceName -ErrorAction Stop

    if ($svc.Status -eq "Stopped") {
        Write-Log ("Service '{0}' is Stopped. Attempting to start..." -f $ServiceName)
        try {
            Start-Service -Name $ServiceName -ErrorAction Stop

            # Wait up to 20 seconds for Running state
            $statusEnum = [System.ServiceProcess.ServiceControllerStatus]::Running
            $timeout    = [TimeSpan]::FromSeconds(20)
            $svc.Refresh()
            $svc.WaitForStatus($statusEnum, $timeout)

            $svc = Get-Service -Name $ServiceName
            if ($svc.Status -eq "Running") {
                Write-Log ("Service '{0}' started successfully." -f $ServiceName)
                try {
                    Write-EventLog -LogName $EventLogName -Source $EventSource -EventId 1000 -EntryType Information -Message "GDsvc was stopped and has been started by the monitor."
                } catch {}
            } else {
                Write-Log ("Service '{0}' start attempt did not reach Running state. Current: {1}" -f $ServiceName, $svc.Status)
                try {
                    Write-EventLog -LogName $EventLogName -Source $EventSource -EventId 1001 -EntryType Warning -Message ("GDsvc start attempted but service is not Running. Current: " + $svc.Status)
                } catch {}
            }
        } catch {
            Write-Log ("ERROR: Failed to start service '{0}'. {1}" -f $ServiceName, $_)
            try {
                Write-EventLog -LogName $EventLogName -Source $EventSource -EventId 1002 -EntryType Error -Message ("GDsvc failed to start. Error: " + $_)
            } catch {}
        }
    } elseif ($svc.Status -eq "Running") {
        # Silent when healthy to keep log small
    } else {
        Write-Log ("Service '{0}' is in state: {1}" -f $ServiceName, $svc.Status)
    }
} catch {
    Write-Log ("ERROR: Could not query service '{0}'. {1}" -f $ServiceName, $_)
    try {
        Write-EventLog -LogName $EventLogName -Source $EventSource -EventId 1003 -EntryType Error -Message ("GDsvc monitor could not query service. Error: " + $_)
    } catch {}
}
