param (
    [string]$ConfigPath = "C:\Development\Scripts\ArchiveConfig.json",
    [string]$SourceListPath = "C:\Development\Scripts\SourceFolders.csv"
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
$logFilePath = $config.LogFilePath

# Initialize directory logs hashtable
$directoryLogs = @{}

# Ensure log file directory exists
$logDir = Split-Path $logFilePath -Parent
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

# Start with a new log file or append to existing one
if (-not (Test-Path $logFilePath)) {
    New-Item -ItemType File -Path $logFilePath -Force | Out-Null
}

# Function to write messages to both console and log file
function Write-Log {
    param (
        [string]$Message
    )
    # Write to console
    Write-Host $Message

    # Append timestamped message to log file
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $logEntry = "$timestamp $Message"
    Add-Content -Path $logFilePath -Value $logEntry
}

# Function to send email notifications
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

# Function to check if a file should be excluded based on patterns
function IsExcluded {
    param (
        [string]$FileName
    )
    foreach ($pattern in $excludePatterns) {
        if ($FileName -like $pattern) {
            Write-Log "Excluding file: $FileName (matched pattern: $pattern)"
            return $true
        }
    }
    Write-Log "Including file: $FileName"
    return $false
}

# Read list of source directories and business emails from CSV file
try {
    $sourceList = Import-Csv -Path $SourceListPath
} catch {
    $errorMessage = "Error reading source list CSV file at $SourceListPath. Error: $_"
    Write-Log $errorMessage
    Send-AdminEmail -Subject "Archive Script Error" -Body $errorMessage
    exit
}

# Process each source directory and associated business email
foreach ($entry in $sourceList) {
    $sourcePath = $entry.'Source Path'
    $perDirectoryLogContactEmail = $entry.'Business Email'

    Write-Log "Processing source: $sourcePath"
    Write-Log "Business Email: $perDirectoryLogContactEmail"

    # Validate source path
    if (-not (Test-Path $sourcePath)) {
        $errorMessage = "Source path does not exist: $sourcePath"
        Write-Log $errorMessage
        $changesLog += $errorMessage
        continue
    }

    $cutOffDate = (Get-Date).AddDays(-$fileAgeInDays)
    Write-Log "Cut off date: $cutOffDate"

    # Get the root of the source path
    $sourceRoot = (Get-Item -Path $sourcePath -Force).PSDrive.Root

    # Get list of files older than the specified age and not excluded
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
    foreach ($item in $items) {
        $lastAccessed = $item.LastAccessTime
        Write-Log "$($item.Name) was last accessed on $lastAccessed"

        # Calculate relative path from the root of the source path
        $relativePath = $item.FullName.Substring($sourceRoot.Length).TrimStart('\')
        $destItemPath = Join-Path $destinationPath $relativePath

        # Ensure destination directory exists
        $destDir = Split-Path $destItemPath -Parent
        if (-not (Test-Path $destDir)) {
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
        }

        # Append to audit log with status 'Initiated'
        $logEntry = '"{0}","{1}","{2}","{3}"' -f (Get-Date), $item.FullName, $destItemPath, 'Initiated'
        Add-Content -Path $geoDriveAuditLogPath -Value $logEntry

        # Copy file with robocopy and error handling
        $copySuccess = $false
        for ($attempt = 1; $attempt -le 2; $attempt++) {
            try {
                # Prepare robocopy command
                $sourceDir = Split-Path $item.FullName -Parent
                $destDir = Split-Path $destItemPath -Parent
                $fileName = $item.Name

                # Ensure destination directory exists
                if (-not (Test-Path $destDir)) {
                    New-Item -ItemType Directory -Path $destDir -Force | Out-Null
                }

                # Construct robocopy argument list
                $robocopyArgs = @(
                    '"' + $sourceDir + '"'   # Source directory (in quotes to handle spaces)
                    '"' + $destDir + '"'     # Destination directory (in quotes to handle spaces)
                    '"' + $fileName + '"'    # File to copy (in quotes to handle spaces)
                    '/COPY:DAT'              # Copy Data, Attributes, and Timestamps
                    '/R:2'                   # Retry 2 times on failure
                    '/W:5'                   # Wait 5 seconds between retries
                    '/NP'                    # No Progress - don't display percentage copied
                    '/NFL'                   # No File List - don't log file names
                    '/NDL'                   # No Directory List - don't log directory names
                    '/NJH'                   # No Job Header - suppress job header
                    '/NJS'                   # No Job Summary - suppress job summary
                )

                # Execute robocopy command
                Write-Log "Executing robocopy for file: $($item.FullName)"
                $robocopyProcess = Start-Process -FilePath 'robocopy.exe' -ArgumentList $robocopyArgs -Wait -NoNewWindow -PassThru
                $robocopyExitCode = $robocopyProcess.ExitCode

                # Check exit code (0 and 1 are considered success)
                if ($robocopyExitCode -eq 0 -or $robocopyExitCode -eq 1) {
                    # Verify copy by comparing file sizes
                    if ((Get-Item -Path $item.FullName -Force).Length -eq (Get-Item -Path $destItemPath -Force).Length) {
                        $copySuccess = $true
                        break
                    } else {
                        throw "File size mismatch after copy."
                    }
                } else {
                    throw "Robocopy failed with exit code $robocopyExitCode."
                }
            } catch {
                if ($attempt -eq 2) {
                    # Log error after final attempt
                    $errorMessage = "Failed to archive file: $($item.FullName). Error: $_"
                    $changesLog += $errorMessage
                    # Update audit log with status 'Failed'
                    $logEntry = '"{0}","{1}","{2}","{3}"' -f (Get-Date), $item.FullName, $destItemPath, 'Failed'
                    Add-Content -Path $geoDriveAuditLogPath -Value $logEntry
                    # Email admin with error
                    Send-AdminEmail -Subject "Archive Script Error" -Body $errorMessage
                } else {
                    # Wait before retrying
                    Start-Sleep -Seconds 5
                }
            }
        }

        if ($copySuccess) {
            # Update audit log with status 'Success'
            $logEntry = '"{0}","{1}","{2}","{3}"' -f (Get-Date), $item.FullName, $destItemPath, 'Success'
            Add-Content -Path $geoDriveAuditLogPath -Value $logEntry
            $changesLog += "Archived file: $($item.FullName) to $destItemPath"

            # Update per-directory logs
            $parentDirectory = Split-Path $item.FullName -Parent
            if (-not $directoryLogs.ContainsKey($parentDirectory)) {
                $directoryLogs[$parentDirectory] = @()
            }
            $directoryLogs[$parentDirectory] += [PSCustomObject]@{
                LastAccessed = $lastAccessed.ToString('yyyy-MM-dd')
                File         = $item.Name
                NewLocation  = $destItemPath
            }

            # Delete original file
            try {
                Remove-Item -Path $item.FullName -Force -ErrorAction Stop
            } catch {
                $errorMessage = "Failed to delete original file: $($item.FullName). Error: $_"
                $changesLog += $errorMessage
                Write-Log $errorMessage
                Send-AdminEmail -Subject "Archive Script Error" -Body $errorMessage
            }
        }
    }

    # Write per-directory CSV logs
    foreach ($directory in $directoryLogs.Keys) {
        try {
            # Use the configured per-directory log file name
            $csvFilePath = Join-Path $directory $perDirectoryLogFileName
            $logEntries = $directoryLogs[$directory]

            # Prepare header lines
            $headerLines = @(
                'Files have been automatically archived after not being accessed for 5 years.',
                "Contact $perDirectoryLogContactEmail if you require access to these files.",
                ''
            )

            # Convert log entries to CSV format
            $csvContent = $logEntries | ConvertTo-Csv -NoTypeInformation

            # Combine header lines and CSV content
            $fullContent = $headerLines + $csvContent

            # Write or append to the CSV file
            if (-not (Test-Path $csvFilePath)) {
                # Write all content if file doesn't exist
                $fullContent | Set-Content -Path $csvFilePath -Encoding UTF8
            } else {
                # Append only CSV content if file exists, skipping headers
                $csvContent | Select -Skip 1 | Add-Content -Path $csvFilePath -Encoding UTF8
            }

            Write-Log "Updated archive CSV log in $directory"
        } catch {
            $errorMessage = "Failed to write archive CSV log in $directory. Error: $_"
            Write-Log $errorMessage
            $changesLog += $errorMessage
            Send-AdminEmail -Subject "Archive Script Error" -Body $errorMessage
        }
    }

    # Clear the directory logs for the next source path
    $directoryLogs.Clear()
}

# Email admin with all changes
if ($changesLog.Count -gt 0) {
    $changesBody = $changesLog -join "`n"
    Send-AdminEmail -Subject $emailSettings.Subject -Body $changesBody
} else {
    Send-AdminEmail -Subject $emailSettings.Subject -Body "No files were archived during this run."
}
