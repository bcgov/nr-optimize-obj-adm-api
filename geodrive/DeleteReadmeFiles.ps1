
# Define variables
$targetPath = "\\sfp.idir.bcgov\S140\S40086\WANSHARE"
$logDir = "E:\Logfiles"
$date = Get-Date -Format "yyyy-MM-dd"
$logFile = Join-Path $logDir "${date}_readme_deleted_S40086_WANSHARE.log"

# Ensure log directory exists
if (-not (Test-Path $logDir)) {
    New-Item -Path $logDir -ItemType Directory -Force
}

# Initialize log content
"Log started on $(Get-Date)" | Out-File -FilePath $logFile

# Search and delete files
try {
    $files = Get-ChildItem -Path $targetPath -Recurse -File -ErrorAction Stop |
             Where-Object { $_.Name -like "*_Readme - Record of Migrated Files.csv" }

    foreach ($file in $files) {
        try {
            Remove-Item -Path $file.FullName -Force -ErrorAction Stop
            "Deleted: $($file.FullName)" | Out-File -FilePath $logFile -Append
        } catch {
            "Error deleting $($file.FullName): $_" | Out-File -FilePath $logFile -Append
        }
    }

    "Log completed on $(Get-Date)" | Out-File -FilePath $logFile -Append
} catch {
    "Error during file search: $_" | Out-File -FilePath $logFile -Append
}

# Output the location of the log file
Write-Output "The log file is located at $logFile"
