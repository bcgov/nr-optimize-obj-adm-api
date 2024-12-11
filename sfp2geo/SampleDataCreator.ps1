 # Set up test root path
$testRootPath = "Z:\TestData"

# Remove existing test data if any
if (Test-Path $testRootPath) {
    Remove-Item -Path $testRootPath -Recurse -Force
}

# Create the root directory
New-Item -ItemType Directory -Path $testRootPath -Force | Out-Null

# Define how many projects and subfolders you want
$numProjects = 1            # Number of top-level project folders
$numSubFoldersPerProject = 2  # Number of subfolders per project
$numFilesPerDirectory = 2     # How many sets of test files per directory

# Build directory structure dynamically
$directories = @()
for ($i = 1; $i -le $numProjects; $i++) {
    $projectDir = Join-Path $testRootPath ("Project_$i")
    $directories += $projectDir
    for ($j = 1; $j -le $numSubFoldersPerProject; $j++) {
        $subDir = Join-Path $projectDir ("SubFolder$j")
        $directories += $subDir
    }
}

# Create directories
foreach ($dir in $directories) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
}

# Create an additional deeply nested directory to exceed path length
$longDirName = "ThisIsAVeryLongDirectoryNameThatWillHelpUsExceedTheWindowsPathLimitByBeingVeryLong_" + ('X' * 100)
foreach ($dir in $directories) {
    $veryLongDir = Join-Path $dir $longDirName
    New-Item -ItemType Directory -Path $veryLongDir -Force | Out-Null
    $directories += $veryLongDir
}

# Set the cutoff date
$fileAgeInDays = 912  # 2.5 years
$cutoffDate = (Get-Date).AddDays(-$fileAgeInDays)

# Counters for total files and files that should be archived
$totalFiles = 0
$filesToArchive = 0

# Function to create test files
function New-TestFile {
    param (
        [string]$Path,
        [string]$Name,
        [string]$Content = "Sample content",
        [DateTime]$LastAccessTime,
        [DateTime]$CreationTime,
        [DateTime]$LastWriteTime,
        [bool]$IsReadOnly = $false,
        [bool]$IsHidden = $false,
        [DateTime]$cutOffDate
    )
    $filePath = Join-Path $Path $Name
    # Create the file with specified content
    Set-Content -Path $filePath -Value $Content
    $fileItem = Get-Item -Path $filePath -Force
    # Set timestamps
    $fileItem.CreationTime = $CreationTime
    $fileItem.LastWriteTime = $LastWriteTime
    $fileItem.LastAccessTime = $LastAccessTime
    # Set file attributes
    if ($IsReadOnly) {
        $fileItem.Attributes += 'ReadOnly'
    }
    if ($IsHidden) {
        $fileItem.Attributes += 'Hidden'
    }

    # Update counters
    $script:totalFiles++
    if ($LastAccessTime -lt $cutOffDate) {
        $script:filesToArchive++
    }
}

# Generate files in each directory
foreach ($dir in $directories) {
    for ($f = 1; $f -le $numFilesPerDirectory; $f++) {
        # Files older than the cutoff date (to be archived)
        New-TestFile -Path $dir -Name ("OldFile$f.txt") -Content "Old file content" `
            -LastAccessTime ($cutoffDate.AddDays(-10)) -CreationTime ($cutoffDate.AddDays(-20)) `
            -LastWriteTime ($cutoffDate.AddDays(-15)) -cutOffDate $cutoffDate

        # Files newer than the cutoff date (should not be archived)
        New-TestFile -Path $dir -Name ("RecentFile$f.txt") -Content "Recent file content" `
            -LastAccessTime (Get-Date) -CreationTime ((Get-Date).AddDays(-10)) `
            -LastWriteTime ((Get-Date).AddDays(-5)) -cutOffDate $cutoffDate

        # Files matching exclusion patterns (should not be archived)
        New-TestFile -Path $dir -Name ("ExcludedFile_HR_$f") -Content "Excluded content" `
            -LastAccessTime ($cutoffDate.AddDays(-30)) -CreationTime ($cutoffDate.AddDays(-40)) `
            -LastWriteTime ($cutoffDate.AddDays(-35)) -cutOffDate $cutoffDate

        # Read-only files
        New-TestFile -Path $dir -Name ("ReadOnlyFile$f.txt") -Content "Read-only file" `
            -LastAccessTime ($cutoffDate.AddDays(-50)) -CreationTime ($cutoffDate.AddDays(-60)) `
            -LastWriteTime ($cutoffDate.AddDays(-55)) -IsReadOnly $true -cutOffDate $cutoffDate

        # Hidden files
        New-TestFile -Path $dir -Name ("HiddenFile$f.txt") -Content "Hidden file" `
            -LastAccessTime ($cutoffDate.AddDays(-70)) -CreationTime ($cutoffDate.AddDays(-80)) `
            -LastWriteTime ($cutoffDate.AddDays(-75)) -IsHidden $true -cutOffDate $cutoffDate

        # Large files (1 MB of 'A's)
        $largeContent = 'A' * 1048576
        New-TestFile -Path $dir -Name ("LargeFile$f.bin") -Content $largeContent `
            -LastAccessTime ($cutoffDate.AddDays(-90)) -CreationTime ($cutoffDate.AddDays(-100)) `
            -LastWriteTime ($cutoffDate.AddDays(-95)) -cutOffDate $cutoffDate
    }

    # Create one extremely long filename in the long directory to exceed 256 chars
    if ($dir -like "*ThisIsAVeryLongDirectoryNameThatWillHelpUsExceedTheWindowsPathLimitByBeingVeryLong_*") {
        $extremelyLongFileName = "ExtremelyLongFileNameToExceedPathLength_" + ('Y' * 200) + ".txt"
        New-TestFile -Path $dir -Name $extremelyLongFileName -Content "Very long path test" `
            -LastAccessTime ($cutoffDate.AddDays(-110)) -CreationTime ($cutoffDate.AddDays(-120)) `
            -LastWriteTime ($cutoffDate.AddDays(-115)) -cutOffDate $cutoffDate
    }
}

# List the generated files (uncomment if needed)
#Get-ChildItem -Path $testRootPath -Recurse -Force | Select-Object FullName, LastAccessTime, CreationTime, Attributes

# Output the summary
Write-Host "Total files generated: $totalFiles"
Write-Host "Files older than $fileAgeInDays days (should be archived): $filesToArchive"
 
