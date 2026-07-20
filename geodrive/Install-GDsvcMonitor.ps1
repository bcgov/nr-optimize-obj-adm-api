<#
Install-GDsvcMonitor.ps1
Installs a scheduled monitor for the GDsvc service on Windows Server 2016:
- Writes E:\scripts\Monitor-GDsvc.ps1
- Registers a Scheduled Task that runs every 5 minutes for 6 months (182 days)
- Configures Service Recovery (crash restart)
- Logs all steps to E:\LogFiles\GeoDrive\Monitoring\Install-GDsvcMonitor.log

Usage (elevated):
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File E:\scripts\Install-GDsvcMonitor.ps1

Uninstall:
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File E:\scripts\Install-GDsvcMonitor.ps1 -Uninstall
#>

[CmdletBinding(SupportsShouldProcess=$false)]
param(
    [switch]$Uninstall,

    # Defaults match your setup.
    [string]$ServiceName    = 'GDsvc',
    [string]$ScriptPath     = 'E:\scripts\Monitor-GDsvc.ps1',
    [string]$LogFolder      = 'E:\LogFiles\GeoDrive\Monitoring',
    [string]$TaskName       = 'Monitor-GDsvc',
    [int]$IntervalMinutes   = 5,      # How often to run
    [int]$DurationDays      = 182     # ~6 months
)

function Assert-Admin {
    $wid = [Security.Principal.WindowsIdentity]::GetCurrent()
    $prp = New-Object Security.Principal.WindowsPrincipal($wid)
    if (-not $prp.IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)) {
        Write-Error 'This script must be run as Administrator.'
        exit 1
    }
}

function Ensure-Folder {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
        Write-Host "Created folder: $Path"
    } else {
        Write-Host "Folder exists:  $Path"
    }
}

function Test-FolderWritable {
    param([string]$Path)
    try {
        if (-not (Test-Path -LiteralPath $Path)) { return $false }
        $probe = Join-Path $Path ('.__writetest_{0}.tmp' -f ([Guid]::NewGuid().ToString('N')))
        Set-Content -LiteralPath $probe -Value 'probe' -Encoding ASCII -Force
        Remove-Item -LiteralPath $probe -Force
        return $true
    } catch {
        return $false
    }
}

function Stop-Transcript-Safe {
    try { if ($global:transcribing) { Stop-Transcript | Out-Null } } catch {}
}

try {
    Assert-Admin

    # Ensure base folders exist so transcript can open.
    $scriptFolder = Split-Path -Path $ScriptPath -Parent
    Ensure-Folder -Path $scriptFolder
    Ensure-Folder -Path $LogFolder

    # Validate writability before proceeding
    if (-not (Test-FolderWritable -Path $scriptFolder)) {
        throw "Folder is not writable: $scriptFolder"
    }
    if (-not (Test-FolderWritable -Path $LogFolder)) {
        throw "Folder is not writable: $LogFolder"
    }

    $TranscriptPath = Join-Path $LogFolder 'Install-GDsvcMonitor.log'
    try {
        Start-Transcript -Path $TranscriptPath -Append | Out-Null
        $global:transcribing = $true
    } catch {
        Write-Warning "Could not open transcript at $TranscriptPath. Continuing without transcript."
        $global:transcribing = $false
    }

    Write-Host '--- Install-GDsvcMonitor: START ---'
    Write-Host "ServiceName:       $ServiceName"
    Write-Host "ScriptPath:        $ScriptPath"
    Write-Host "LogFolder:         $LogFolder"
    Write-Host "TaskName:          $TaskName"
    Write-Host "IntervalMinutes:   $IntervalMinutes"
    Write-Host "DurationDays:      $DurationDays"

    if ($Uninstall) {
        Write-Host 'Uninstall requested.'

        # Remove Scheduled Task if present
        try {
            $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
            if ($task) {
                Write-Host "Removing scheduled task: $TaskName"
                Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
            } else {
                Write-Host "Scheduled task not found: $TaskName"
            }
        } catch {
            Write-Warning ("Failed to remove scheduled task. {0}" -f $_)
        }

        # Optionally remove monitor script (comment out to keep it)
        if (Test-Path -LiteralPath $ScriptPath) {
            try {
                Remove-Item -LiteralPath $ScriptPath -Force
                Write-Host "Removed script: $ScriptPath"
            } catch {
                Write-Warning "Could not remove script at $ScriptPath. $_"
            }
        } else {
            Write-Host "Script not found: $ScriptPath"
        }

        Write-Host 'Uninstall complete.'
        return
    }

    # Pre-flight: confirm service exists
    $svc = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if (-not $svc) {
        throw "Service '$ServiceName' not found. Install or correct the service name and re-run."
    } else {
        Write-Host "Found service: $($svc.DisplayName) [$ServiceName]"
    }

    # Write the monitor script (ASCII encoding as requested)
    $monitorScript = @'
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
'@

    Set-Content -LiteralPath $ScriptPath -Value $monitorScript -Encoding ASCII -Force
    Write-Host "Wrote monitor script to: $ScriptPath (ASCII)"

    # Create or update Scheduled Task (hardened)
    try {
        $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($existing) {
            Write-Host "Existing scheduled task found. Removing: $TaskName"
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        }
    } catch {
        Write-Warning ("Could not query/remove existing scheduled task. {0}" -f $_)
    }

    $action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument ("-NoProfile -ExecutionPolicy Bypass -File `"{0}`"" -f $ScriptPath)

    # StartBoundary must be >= now; add 1 minute for safety
    # Optional hardening: make sure the DateTime kind is Local (explicit)
    $startTime = [datetime]::SpecifyKind((Get-Date).AddMinutes(1), [System.DateTimeKind]::Local)

    $trigger = New-ScheduledTaskTrigger -Once -At $startTime `
        -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) `
        -RepetitionDuration (New-TimeSpan -Days $DurationDays)

    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew
    $principal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -RunLevel Highest -LogonType ServiceAccount

    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal | Out-Null
    Write-Host "Registered scheduled task: $TaskName (every $IntervalMinutes minutes, for $DurationDays days)"

    # Configure Windows Service Recovery (handles crashes)
    try {
        & sc.exe failure $ServiceName 'reset= 86400' 'actions= restart/60000/restart/60000/restart/60000' | Out-Null
        & sc.exe failureflag $ServiceName 1 | Out-Null
        Write-Host "Configured Service Recovery for $ServiceName (auto-restart on failures)."
    } catch {
        Write-Warning ("Failed to configure Service Recovery with sc.exe. {0}" -f $_)
    }

    # Optional: test-run once
    try {
        Start-ScheduledTask -TaskName $TaskName
        Write-Host "Triggered first run of task: $TaskName"
    } catch {
        Write-Warning ("Could not start the scheduled task immediately. {0}" -f $_)
    }

    Write-Host '--- Install-GDsvcMonitor: COMPLETE ---'
    Write-Host "Check log: $LogFolder\GDsvc-monitor.log (after first task run)."
    Write-Host "Installer transcript: $TranscriptPath"
}
finally {
    Stop-Transcript-Safe
}
