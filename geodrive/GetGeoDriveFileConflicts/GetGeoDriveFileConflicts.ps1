# Server dependent script variables:
$outputDir = "\\warehouse\optimization\6 - Object Storage\GeoDrive\BucketReport"
$gdcli = "E:\Program Files\Dell GeoDrive\exe\gd_cli.exe"
$cachePathRegex = "^(E:\\GeoDriveCache\\.+)"

# Server name for file naming
$serverName = $env:COMPUTERNAME

# Date-based subfolder (yyyy-MM-dd)
$runDate = (Get-Date).ToString("yyyy-MM-dd")
$dateDir = Join-Path $outputDir $runDate

# ------------------------------------------------------------
# 1. PARSE GEO DRIVE CONFIGS
# ------------------------------------------------------------
# Base output directory

$raw = & $gdcli Drive /list /v

$drives = @()
$current = $null
$inFSLog = $false
$inRules = $false

# Break out early for development:
$driveCount = 0
foreach ($line in $raw) {

    # ---------------------- NEW DRIVE (CachePath) ----------------------
    if ($line -match $cachePathRegex) {

    
        # Break out early for development. Stop after first 5 drives (development mode)
        $driveCount++
        if ($driveCount -gt 300) {
            break  # exits the foreach loop completely
        }


        # Save previous drive
        if ($current) { $drives += $current }

        # Create new empty object
        $current = [PSCustomObject]@{
            CachePath       = $Matches[1].Trim()
            CloudHost       = $null
            Bucket          = $null
            ConfigID        = $null
            Enabled         = $null
            Description     = $null
            BucketSignature = $null
            Settings        = @{}
            FSLog           = @{
                Enabled    = $false
                Path       = $null
                MaxSize    = $null
                MaxLogs    = $null
                MinFree    = $null
                Operations = @{}
            }
            Rules = @()
        }

        $inFSLog = $false
        $inRules = $false
        continue
    }

    if (-not $current) { continue }

    # ---------------------- CLOUD HOST ----------------------
    if ($line -match "Cloud Host:\s+(.+)$") {
        $current.CloudHost = $Matches[1].Trim()
        continue
    }

    # ---------------------- BUCKET ----------------------
    if ($line -match "^\s+Bucket:\s+(\S+)$") {
        $current.Bucket = $Matches[1]
        continue
    }

    # ---------------------- CONFIG ID ----------------------
    if ($line -match "Config ID:\s+(.+)$") {
        $current.ConfigID = $Matches[1].Trim()
        continue
    }

    # ---------------------- ENABLED / DISABLED ----------------------
    if ($line -match "^\s*Enabled$")  { $current.Enabled = $true;  continue }
    if ($line -match "^\s*Disabled$") { $current.Enabled = $false; continue }

    # ---------------------- DESCRIPTION ----------------------
    if ($line -match "Description:\s+(.+)$") {
        $current.Description = $Matches[1].Trim()
        continue
    }

    # ---------------------- BUCKET SIGNATURE ----------------------
    if ($line -match "BucketSignature:\s+(.+)$") {
        $current.BucketSignature = $Matches[1].Trim()
        continue
    }

    # ---------------------- GENERAL SETTINGS ----------------------
    if ($line -match "^\s*([^:]+):\s+(.+)$" -and
        $line -notmatch "^File System Logging" -and
        $line -notmatch "^Rules:" -and
        $line -notmatch "^\s+Bucket:"
    ) {
        $key = $Matches[1].Trim()
        $val = $Matches[2].Trim()

        if ($val -eq "Yes")      { $val = $true  }
        elseif ($val -eq "No")   { $val = $false }

        $current.Settings[$key] = $val
        continue
    }

    # ---------------------- FILE SYSTEM LOGGING ----------------------
    if ($line -match "File System Logging Enabled") {
        $current.FSLog.Enabled = $true
        $inFSLog = $true
        $inRules = $false
        continue
    }

    if ($inFSLog -and $line -match "^\s+(.+)$") {
        $fsline = $Matches[1].Trim()

        if ($fsline -match "^(E:.+)$") {
            $current.FSLog.Path = $Matches[1]
            continue
        }
        if ($fsline -match "^Maximum Log Size:\s+(.+)$") {
            $current.FSLog.MaxSize = $Matches[1]
            continue
        }
        if ($fsline -match "^Maximum Log Files:\s+(.+)$") {
            $current.FSLog.MaxLogs = $Matches[1]
            continue
        }
        if ($fsline -match "^Minimum Free Space:\s+(.+)$") {
            $current.FSLog.MinFree = $Matches[1]
            continue
        }
        if ($fsline -match "^(.+):\s+(Yes|No)$") {
            $current.FSLog.Operations[$Matches[1].Trim()] =
                ($Matches[2] -eq "Yes")
            continue
        }
    }

    # ---------------------- RULES ----------------------
    if ($line -match "^\s*Rules:") {
        $inRules = $true
        $inFSLog = $false
        continue
    }

    if ($inRules -and $line -match "^\s+(.+)$") {
        $current.Rules += $Matches[1].Trim()
        continue
    }
}

# Save last block
if ($current) { $drives += $current }


# ------------------------------------------------------------
# 2. SECOND PASS — ADD SHARE INFORMATION
# ------------------------------------------------------------

# Get all share information at once
$allShares = Get-WmiObject -Class Win32_Share | Where-Object { $_.Path }

foreach ($d in $drives) {
    
# Normalize cache path once
    $cachePathNormalized = $d.CachePath.TrimEnd('\').ToLowerInvariant()

    $shareNames = $allShares |
        Where-Object {
            $_.Path.TrimEnd('\').ToLowerInvariant() -eq $cachePathNormalized
        } |
        Select-Object -ExpandProperty Name

    # Deduplicate defensively (just in case)
    $shareNames = $shareNames | Sort-Object -Unique

    $d | Add-Member -MemberType NoteProperty -Name Shares -Value $shareNames

}

# ------------------------------------------------------------
# 3. THIRD PASS — FIND RECENT CSV FSLog FILES + SUMMARIZE OPERATIONS
# ------------------------------------------------------------

$cutoff = (Get-Date).AddDays(-7)

foreach ($d in $drives) {
    
    # Skipping for Dev
    break

    $fsPath = $d.FSLog.Path
    $recentLogs = @()
    $operationCounts = @{}

    if ($fsPath -and (Test-Path $fsPath)) {

        try {
            # Get CSV files modified within the last week
            $recentLogs = Get-ChildItem -Path $fsPath -Filter *.csv -File |
                Where-Object { $_.LastWriteTime -ge $cutoff } |
                Select-Object -ExpandProperty FullName
        }
        catch {
            $recentLogs = @()
        }

        foreach ($log in $recentLogs) {
            try {
                # Read all lines manually
                $lines = Get-Content $log

                # Skip the first "Path:" line
                if ($lines.Count -lt 2) { continue }

                $csvHeader = $lines[1]            # Real header
                $csvData   = $lines[2..($lines.Count - 1)]

                # Import CSV from the string block with proper header
                $rows = $csvData | ConvertFrom-Csv -Header ($csvHeader -split ",")

                foreach ($row in $rows) {
                    $op = $row.Operation

                    if ([string]::IsNullOrWhiteSpace($op)) { continue }

                    if ($operationCounts.ContainsKey($op)) {
                        $operationCounts[$op] += 1
                    } else {
                        $operationCounts[$op] = 1
                    }
                }
            }
            catch {
                # If one CSV fails, just skip it
            }
        }
    }

    # Add discovered properties to this drive
    $d | Add-Member -MemberType NoteProperty -Name RecentFSLogs -Value $recentLogs
    $d | Add-Member -MemberType NoteProperty -Name OperationSummary -Value $operationCounts
}

# ------------------------------------------------------------
# 4. FOURTH PASS — FIND UPPERCASE PATH ERRORS IN WINDOWS EVENT LOG
# ------------------------------------------------------------

# Error text we are looking for
$targetText = "Files/Folders name cannot contain upper case characters - this file will not be accessible"

# Look back window (adjust if desired)
$eventCutoff = (Get-Date).AddDays(-7)

# Pull relevant Application log events once
$geoDriveEvents = Get-WinEvent -FilterHashtable @{
    LogName      = 'Application'
    ProviderName = 'Dell GeoDrive Service'
    StartTime    = $eventCutoff
} | Where-Object {
    $_.Message -like "*$targetText*"
}

foreach ($d in $drives) {

    # Initialize output collection
    $d | Add-Member -MemberType NoteProperty -Name UppercasePathErrors -Value @()

    # CachePath for matching (normalized)
    $cachePathLower = $d.CachePath.ToLowerInvariant()

    # Deduplication lookup (per drive)
    $seenPaths = @{}

    foreach ($evt in $geoDriveEvents) {

        $msg = $evt.Message

        # Extract the local file path from the message
        $pathMatch = [System.Text.RegularExpressions.Regex]::Match(
            $msg,
            "accessible:\s*(?<path>[A-Za-z]:\\.+?)\s+Cloud Path:",
            [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
        )

        if (-not $pathMatch.Success) { continue }

        $eventPath = $pathMatch.Groups['path'].Value.Trim()
        $eventPathLower = $eventPath.ToLowerInvariant()

        # Must belong to this GeoDrive cache
        if (-not $eventPathLower.StartsWith($cachePathLower)) { continue }

        # Dedup: only add if we haven't seen this path before
        if (-not $seenPaths.ContainsKey($eventPathLower)) {
            $seenPaths[$eventPathLower] = $true
            $d.UppercasePathErrors += $eventPath
        }
    }
}

# ------------------------------------------------------------
# 5. OUTPUT RESULT — CSV FILES TO DATE SUBFOLDER
# ------------------------------------------------------------

# Ensure base and date subfolder exist
if (-not (Test-Path $dateDir)) {
    New-Item -ItemType Directory -Path $dateDir -Force | Out-Null
}

# File paths (written into date subfolder)
$summaryCsv  = Join-Path $dateDir "${runDate}_${serverName}_GD_Summary.csv"
$conflictCsv = Join-Path $dateDir "${runDate}_${serverName}_File_Conflicts.csv"


# Gather data for GD_Summary CSV - One row per CachePath
$gdSummary = foreach ($d in $drives) {
    [PSCustomObject]@{
        CachePath   = $d.CachePath
        CloudHost   = $d.CloudHost
        Bucket      = $d.Bucket
        Enabled     = $d.Enabled
        Description = $d.Description
        Shares      = ($d.Shares -join '; ')
    }
}

# Create Summary CSV
$gdSummary |
    Export-Csv -Path $summaryCsv -NoTypeInformation -Encoding UTF8


# Gather data for File_Conflicts CSV - One row per UppercasePathError
$fileConflicts = foreach ($d in $drives) {
    foreach ($path in $d.UppercasePathErrors) {
        [PSCustomObject]@{
            Bucket             = $d.Bucket
            UppercasePathError = $path
        }
    }
}

# Always create the conflicts CSV (even if empty, headers are useful)
if ($fileConflicts) {
    $fileConflicts |
        Export-Csv -Path $conflictCsv -NoTypeInformation -Encoding UTF8
} else {
    [PSCustomObject]@{
        Bucket             = $null
        UppercasePathError = $null
    } |
    Export-Csv -Path $conflictCsv -NoTypeInformation -Encoding UTF8
}

# ------------------------------------------------------------
# 6. SIXTH PASS — SETTINGS REPORT
# ------------------------------------------------------------


# Output paths (same date folder as previous CSVs)
$settingsCsv = Join-Path $dateDir "${runDate}_${serverName}_Drive_Settings.csv"


$allSettingKeys = $drives |
    ForEach-Object { $_.Settings.Keys } |
    Sort-Object -Unique



# SETTINGS REPORT — BUILD ROWS WITH CHECKSUM
# We can use the checksum to group drives with similar configurations (i.e. already standardized)
$settingsReport = foreach ($d in $drives) {

    # Canonicalize settings for checksum:
    # key=value pairs, sorted by key, joined consistently
    $canonicalSettings = $allSettingKeys |
        ForEach-Object {
            if ($d.Settings.ContainsKey($_)) {
                "$_=$($d.Settings[$_])"
            } else {
                "$_="
            }
        }

    $settingsString = $canonicalSettings -join '|'

    # Compute SHA256 checksum
    $hashBytes = [System.Text.Encoding]::UTF8.GetBytes($settingsString)
    $hash      = [System.Security.Cryptography.SHA256]::Create()
    $checksum  = ([System.BitConverter]::ToString(
                    $hash.ComputeHash($hashBytes)
                  )).Replace('-', '').ToLowerInvariant()

    # Build output row
    $row = [ordered]@{
        CachePath       = $d.CachePath
        Bucket          = $d.Bucket
        CloudHost       = $d.CloudHost
        SettingsChecksum = $checksum
    }

    foreach ($key in $allSettingKeys) {
        $row[$key] = if ($d.Settings.ContainsKey($key)) {
            $d.Settings[$key]
        } else {
            $null
        }
    }

    [PSCustomObject]$row
}

# Export Settings CSV
$settingsReport |
    Export-Csv -Path $settingsCsv -NoTypeInformation -Encoding UTF8


# ------------------------------------------------------------
# RULES REPORT
# ------------------------------------------------------------

# Output paths (same date folder as previous CSVs)
$rulesCsv    = Join-Path $dateDir "${runDate}_${serverName}_Drive_Rules.csv"

$allRules = $drives |
    Where-Object { $_.Rules } |
    Select-Object -ExpandProperty Rules |
    Sort-Object -Unique

$drives
    
# RULES REPORT — BUILD ROWS
$rulesReport = foreach ($d in $drives) {

    $row = [ordered]@{
        CachePath = $d.CachePath
        Bucket    = $d.Bucket
        CloudHost = $d.CloudHost
    }

    foreach ($rule in $allRules) {
        $row[$rule] = if ($d.Rules -contains $rule) { $true } else { $null }
    }
    
    [PSCustomObject]$row
}

# Export Rules CSV
$rulesReport |
    Export-Csv -Path $rulesCsv -NoTypeInformation -Encoding UTF8