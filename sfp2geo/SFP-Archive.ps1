 param (
    [string]$ConfigPath = "E:\Scripts\sfp2geo\ArchiveConfig.json",
    [string]$SourceListPath = "E:\Scripts\sfp2geo\SourceFolders.csv"
)

# Load configuration
$config = Get-Content $ConfigPath | ConvertFrom-Json

# Initialize variables
$adminEmail = $config.AdminEmail
$enableEmailNotifications = $config.EnableEmailNotifications
$perDirectoryLogFileName = $config.PerDirectoryLogFileName
$geoDriveAuditLogPath = $config.GeoDriveAuditLogPath
$fileAgeInDays = $config.FileAgeInDays
$excludePatterns = $config.ExcludePatterns
$emailSettings = $config.EmailSettings
$changesLog = @()
$destinationPath = $config.DestinationPath
$objectStorePathPrefix = $config.ObjectStorePathPrefix
$logFilePath = $config.LogFilePath
$helpURL = $config.HelpPageURL

# Initialize directory logs hashtable (stores lists of files archived per directory)
# We'll now handle directory logs after each directory is processed
$directoryLogs = @{}

# Hashtable to store source directory timestamps and destination directory paths
$dirTimestamps = @{}

# Ensure log file directory exists
$logDir = Split-Path $logFilePath -Parent
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

# Start with a new log file or append to existing one
if (-not (Test-Path $logFilePath)) {
    New-Item -ItemType File -Path $logFilePath -Force | Out-Null
}

function Write-Log {
    param ([string]$Message)
    Write-Host $Message
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $logEntry = "$timestamp $Message"
    Add-Content -Path $logFilePath -Value $logEntry
}

function Send-AdminEmail {
    param (
        [string]$Subject,
        [string]$Body
    )
    if ($enableEmailNotifications) {
        Send-MailMessage -SmtpServer $emailSettings.SmtpServer `
                         -From $emailSettings.From `
                         -To $adminEmail `
                         -Subject $Subject `
                         -Body $Body
    } else {
        Write-Log "Email notifications are disabled. Email not sent."
    }
}

function IsExcluded {
    param ([string]$FileName)
    foreach ($pattern in $excludePatterns) {
        if ($FileName -like $pattern) {
            return $true
        }
    }
    return $false
}

try {
    $sourceList = Import-Csv -Path $SourceListPath
} catch {
    $errorMessage = "Error reading source list CSV file at $SourceListPath. Error: $_"
    Write-Log $errorMessage
    Send-AdminEmail -Subject "Archive Script Error" -Body $errorMessage
    exit
}

foreach ($entry in $sourceList) {
    $sourcePath = $entry.'Source Path'
    $perDirectoryLogContactEmail = $entry.'Business Email'

    Write-Log "Processing source: $sourcePath"
    Write-Log "Business Email: $perDirectoryLogContactEmail"

    if (-not (Test-Path $sourcePath)) {
        $errorMessage = "Source path does not exist: $sourcePath"
        Write-Log $errorMessage
        $changesLog += $errorMessage
        continue
    }

    $cutOffDate = (Get-Date).AddDays(-$fileAgeInDays)
    Write-Log "Cut off date: $cutOffDate"

    $sourceRoot = (Get-Item -Path $sourcePath -Force).PSDrive.Root

    try {
        $items = Get-ChildItem -Path $sourcePath -Recurse -File -Force -ErrorAction Stop | Where-Object {
            $_.LastAccessTime -lt $cutOffDate -and -not (IsExcluded $_.Name)
        }
    } catch {
        $errorMessage = "Error accessing source path $sourcePath. Error: $_"
        Write-Log $errorMessage
        Send-AdminEmail -Subject "Archive Script Error" -Body $errorMessage
        continue
    }

    Write-Log "Number of items: $($items.Count)"

    # Group items by their parent directory
    $itemsByDirectory = $items | Group-Object {
        (Split-Path $_.FullName -Parent)
    }

    # Process each directory group
    foreach ($group in $itemsByDirectory) {
        $parentDirectory = $group.Name
        $files = $group.Group

        # Compute $dirTimestamps entry if not done before
        if (-not $dirTimestamps.ContainsKey($parentDirectory)) {
            $sourceDirInfo = Get-Item $parentDirectory
            $relativeDirPath = $parentDirectory.Substring($sourceRoot.Length).TrimStart('\')
            $destDirForParent = Join-Path $destinationPath $relativeDirPath

            $dirTimestamps[$parentDirectory] = [PSCustomObject]@{
                CreationTime   = $sourceDirInfo.CreationTime
                LastAccessTime = $sourceDirInfo.LastAccessTime
                LastWriteTime  = $sourceDirInfo.LastWriteTime
                DestDirPath    = $destDirForParent
            }
        }

        # Process each file in this directory
        foreach ($item in $files) {
            $lastAccessed = $item.LastAccessTime
            $relativePath = $item.FullName.Substring($sourceRoot.Length).TrimStart('\')
            $destItemPath = Join-Path $destinationPath $relativePath
            $parentDir = Split-Path $item.FullName -Parent
            $destDir = Split-Path $destItemPath -Parent

            if (-not (Test-Path $destDir)) {
                New-Item -ItemType Directory -Path $destDir -Force | Out-Null
            }

            # Audit log (Initiated)
            $logEntry = '"{0}","{1}","{2}","{3}"' -f (Get-Date), $item.FullName, $destItemPath, 'Initiated'
            Add-Content -Path $geoDriveAuditLogPath -Value $logEntry

            $copySuccess = $false
            $sourceSize = (Get-Item -Path $item.FullName -Force).Length

            for ($attempt = 1; $attempt -le 2; $attempt++) {
                try {
                    $fileName = $item.Name
                    $sourceDir = Split-Path $item.FullName -Parent

                    $robocopyArgs = @(
                        '"' + $sourceDir + '"'   # Source directory (enclosed in quotes to handle spaces)
                        '"' + $destDir + '"'     # Destination directory (enclosed in quotes to handle spaces)
                        '"' + $fileName + '"'    # Specific file to move (enclosed in quotes for spaces)
                        '/COPY:DATSO'  # Copy Data, Attributes, Timestamps, Security, and Owner information
                        '/R:2'         # Retry copying a file 2 times if an error occurs
                        '/W:5'         # Wait 5 seconds between retries
                        '/NP'          # No Progress - do not display percentage progress for copied files
                        '/NFL'         # No File List - do not list individual files processed
                        '/NDL'         # No Directory List - do not list directories processed
                        '/NJH'         # No Job Header - suppress the job header from the output
                        '/NJS'         # No Job Summary - suppress the job summary from the output
                        '/J'           # Copy using unbuffered I/O for faster throughput (recommended for large files)
                        '/MOV'         # Move files (copy and then delete from source) rather than just copying
                        '/NOOFFLOAD'   # Do not use file offload. Prevents Robocopy from using the Windows offload feature
                    )


                    #Write-Log "---------------"
                    Write-Log "Executing robocopy for file: $($item.FullName)"
                    $robocopyProcess = Start-Process -FilePath 'robocopy.exe' -ArgumentList $robocopyArgs -Wait -NoNewWindow -PassThru
                    $robocopyExitCode = $robocopyProcess.ExitCode

                    if ($robocopyExitCode -eq 0 -or $robocopyExitCode -eq 1) {
                        $destSize = (Get-Item -Path $destItemPath -Force).Length
                        if ($destSize -eq $sourceSize) {
                            $copySuccess = $true
                            Write-Log "Successful robocopy for file: $($item.FullName)"
                            break
                        } else {
                            throw "File size mismatch after move."
                        }
                    } else {
                        throw "Robocopy failed with exit code $robocopyExitCode."
                    }
                } catch {
                    if ($attempt -eq 2) {
                        $errorMessage = "Failed to archive file: $($item.FullName). Error: $_"
                        $changesLog += $errorMessage
                        # Audit log (Failed)
                        $logEntry = '"{0}","{1}","{2}","{3}"' -f (Get-Date), $item.FullName, $destItemPath, 'Failed'
                        Add-Content -Path $geoDriveAuditLogPath -Value $logEntry
                        Send-AdminEmail -Subject "Archive Script Error" -Body $errorMessage
                    } else {
                        Start-Sleep -Seconds 5
                    }
                }
            }

            if ($copySuccess) {
                # Audit log (Success)
                $logEntry = '"{0}","{1}","{2}","{3}"' -f (Get-Date), $item.FullName, $destItemPath, 'Success'
                Add-Content -Path $geoDriveAuditLogPath -Value $logEntry
                $changesLog += "Archived file: $($item.FullName) to $destItemPath"

                # Update directory logs
                if (-not $directoryLogs.ContainsKey($parentDirectory)) {
                    $directoryLogs[$parentDirectory] = @()
                }

                #create a user-friendly file path - need to match \S104 format
                $newDest = $destItemPath -replace '^(.*?)(?=[A-Za-z]\d{3})', $objectStorePathPrefix
                Write-Log "NEW LOCATION: $newDest"

                $directoryLogs[$parentDirectory] += [PSCustomObject]@{
                    LastAccessed = $lastAccessed.ToString('yyyy-MM-dd')
                    File         = $item.Name
                    NewLocation  = $newDest
                }

            }
        }

        # After processing all files in this directory, write the per-directory CSV log and set timestamps

        if ($directoryLogs.ContainsKey($parentDirectory)) {
            #$csvFilePath = Join-Path $dirTimestamps[$parentDirectory].DestDirPath $perDirectoryLogFileName
            $csvFilePath = Join-Path $parentDirectory $perDirectoryLogFileName
            $logEntries = $directoryLogs[$parentDirectory]
            $csvDate =  Get-Date -Format "MMM dd yyyy"

            # CSV header lines
            $headerLines = @(
                'Files have been automatically archived after not being accessed for 2.5 years.,,'
                "Last archive run on:,$csvDate,"
                ',,,'
                "You can create a convenient link to this archive by mapping a network location using the following instructions:,$helpURL,"
                "Share Address:,$objectStorePathPrefix,"
                "Contact $perDirectoryLogContactEmail if you require access to these files.,,"
                ',,,'
            )

            $csvContent = $logEntries | ConvertTo-Csv -NoTypeInformation
            $fullContent = $headerLines + $csvContent

            try {
                if (-not (Test-Path $csvFilePath)) {
                    $fullContent | Set-Content -Path $csvFilePath -Encoding UTF8
                } else {
                    $csvContent | Select -Skip 1 | Add-Content -Path $csvFilePath -Encoding UTF8
                }
                Write-Log "Updated archive CSV log in $parentDirectory"
            } catch {
                $errorMessage = "Failed to write archive CSV log in $parentDirectory. Error: $_"
                Write-Log $errorMessage
                $changesLog += $errorMessage
                Send-AdminEmail -Subject "Archive Script Error" -Body $errorMessage
            }

            # Set the destination directory timestamps
            $ts = $dirTimestamps[$parentDirectory]
            if (Test-Path $ts.DestDirPath) {
                $destDirInfo = Get-Item $ts.DestDirPath
                $destDirInfo.CreationTime   = $ts.CreationTime
                $destDirInfo.LastAccessTime = $ts.LastAccessTime
                $destDirInfo.LastWriteTime  = $ts.LastWriteTime
                Write-Log "Set timestamps on $($ts.DestDirPath) to match source directory $parentDirectory"
            }

            # Clear logs for this directory since we're done
            $directoryLogs.Remove($parentDirectory) | Out-Null
            $dirTimestamps.Remove($parentDirectory) | Out-Null
        }

    } # end of itemsByDirectory loop

} # end of sourceList loop

# Send summary email after processing all sources
if ($changesLog.Count -gt 0) {
    $changesBody = $changesLog -join "`n"
    Send-AdminEmail -Subject $emailSettings.Subject -Body $changesBody
} else {
    Send-AdminEmail -Subject $emailSettings.Subject -Body "No files were archived during this run."
}
 
