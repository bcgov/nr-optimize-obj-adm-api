# Write-Log, Write-InfoLog and Write-ErrorLog work together to allow developers to quickly run a script with varying amounts of logging.
# Usage: Set the logLevel in the main script, and then call Write-InfoLog or Write-ErrorLog to output logs.
# Result: If logLevel is INFO all logs will be generated. If logLevel is ERROR it will skip INFO logs.
function Write-Log {
param ([string]$Type,[string]$Message)
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $logEntry = "$($timestamp),$($Type),$($Message)"
    Add-Content -Path $logFilePath -Value $logEntry
    
    if ($runSilent -eq $false) {
        Write-Host $logEntry
    }
}

function Write-InfoLog {
param ([string]$Message)
    if ($logLevel -eq "INFO") {
        Write-Log "INFO" $Message
    }
}
function Write-ErrorLog {
param ([string]$Message)
    if (($logLevel -eq "INFO") -or ($logLevel -eq "ERROR")) {
        Write-Log "ERROR" $Message
    }
}

# Parse a file path and add the datetime as a suffix before the file extension.
function Add-DateToFilePath {
param (
    [string]$filePath
)
    $dirName  = [io.path]::GetDirectoryName($filePath)
    $filename = [io.path]::GetFileNameWithoutExtension($filePath)
    $ext      = [io.path]::GetExtension($filePath)
    return "$dirName\$filename $(Get-Date -Format 'yyyy-MM-dd HH-mm-ss')$ext"
}

function Write-StandardScriptStart {   
    # Ensure log file directory exists
$logFilePath ="E:\scripts\sfp2geo\Delete-Duplicates-From-Folders\Delete-Duplicate-Source-Files-log.csv"
    write-host $logFilePath

    $logDir = Split-Path $logFilePath -Parent
    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }
    # Add date to log file
    $logFilePath = Add-DateToFilePath($logFilePath)
 
    
    if ($runSilent -eq $false) {
        Write-Host "Script Path: $logFilePath"
        Write-Host "Log File Path: $logFilePath"
        Write-Host "Log Level: $logLevel"
        Write-Host "Silent: $false"
        $runningInfo = $MyInvocation.MyCommand.Path
        if ($runningInfo) {
            Write-Host "Run Command: $runningInfo"
        }
    }
}

function Delete-DirIfEmpty {
param (
    [string]$folderPath
)
    if (Test-Path $folderPath) {
        
        $currentChildren = Get-ChildItem -Force -LiteralPath $folderPath | Select-Object -ExpandProperty Name
        # We literally never care about thumbs.db files. Hard delete if only thing in the folder.
        if ($currentChildren.Count -eq 0) {
            Write-InfoLog("Deleting Empty Folder: ${folderPath}")
            Remove-Item -Force -LiteralPath $folderPath
        } elseif ($currentChildren.Count -eq 1) {
            $firstFile = ($currentChildren | Select-Object -First 1).Name
            if ($firstFile -eq "Thumbs.db"){
                Write-InfoLog("Deleting Thumbs.db and then empty folder at: ${folderPath}")
                $thumbPath = Join-Path -Path $folderPath -ChildPath "Thumbs.db"
                Remove-Item -Force -Path $thumbPath
                Remove-Item -Force -LiteralPath $folderPath
            }
        }
    }
}

function Hard-Delete-File-In-Folder {
param (
    [string]$RootPath,
    [string]$FileName,
    [string]$DeleteEmptyFolder = $false,
    [string]$Recurse = $false
)
    if (Test-Path $RootPath) {
        # Delete the file in the current folder
        $currentFile = Join-Path -Path $RootPath -ChildPath $FileName
        if (Test-Path $currentFile) {
            # Remove-Item -Force -Path $currentFile
        }
        
        # Delete the file in subfolders by calling this function on those folders.
        if ($Recurse) {
            Get-ChildItem -Force -LiteralPath $folderPath -Directory | Select-Object -ExpandProperty Name | ForEach-Object {
                Write-InfoLog($_.Name)
                Write-InfoLog("Checking folder ${$_.Name}")
                if ($currentChildren.Count -eq 0) {
                    Write-InfoLog("Deleting Empty Folder: ${folderPath}")
                    # Remove-Item -Force -LiteralPath $folderPath
                }
            }

        }

    }
}

Export-ModuleMember -Function *