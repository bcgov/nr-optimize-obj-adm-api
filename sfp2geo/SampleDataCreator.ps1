# Set up test root path
$testRootPath = "C:\TestData"

# Remove existing test data if any
if (Test-Path $testRootPath) {
    Remove-Item -Path $testRootPath -Recurse -Force
}

# Create the root directory
New-Item -ItemType Directory -Path $testRootPath -Force | Out-Null

# Define directory structure
$directories = @(
    "$testRootPath\ProjectA",
    "$testRootPath\ProjectA\SubFolder1",
    "$testRootPath\ProjectA\SubFolder2",
    "$testRootPath\ProjectB",
    "$testRootPath\ProjectB\SubFolder1",
    "$testRootPath\ProjectC"
)

# Create directories
foreach ($dir in $directories) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
}

# Set the cutoff date
$fileAgeInDays = 1825  # 5 years
$cutoffDate = (Get-Date).AddDays(-$fileAgeInDays)

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
        [bool]$IsHidden = $false
    )
    $filePath = Join-Path $Path $Name
    # Create the file with specified content
    Set-Content -Path $filePath -Value $Content
    # Get the file item with -Force to include hidden files
    $fileItem = Get-Item -Path $filePath -Force
    # Set timestamps before setting read-only or hidden attributes
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
}

# Generate files in each directory
foreach ($dir in $directories) {
    # Files older than the cutoff date (to be archived)
    New-TestFile -Path $dir -Name "OldFile1.txt" -Content "Old file content" `
        -LastAccessTime ($cutoffDate.AddDays(-10)) -CreationTime ($cutoffDate.AddDays(-20)) `
        -LastWriteTime ($cutoffDate.AddDays(-15))
    
    # Files newer than the cutoff date (should not be archived)
    New-TestFile -Path $dir -Name "RecentFile1.txt" -Content "Recent file content" `
        -LastAccessTime (Get-Date) -CreationTime ((Get-Date).AddDays(-10)) `
        -LastWriteTime ((Get-Date).AddDays(-5))
    
    # Files matching exclusion patterns (should not be archived)
    New-TestFile -Path $dir -Name "ExcludedFile_HR" -Content "Excluded content" `
        -LastAccessTime ($cutoffDate.AddDays(-30)) -CreationTime ($cutoffDate.AddDays(-40)) `
        -LastWriteTime ($cutoffDate.AddDays(-35))
    
    # Read-only files
    New-TestFile -Path $dir -Name "ReadOnlyFile.txt" -Content "Read-only file" `
        -LastAccessTime ($cutoffDate.AddDays(-50)) -CreationTime ($cutoffDate.AddDays(-60)) `
        -LastWriteTime ($cutoffDate.AddDays(-55)) -IsReadOnly $true
    
    # Hidden files
    New-TestFile -Path $dir -Name "HiddenFile.txt" -Content "Hidden file" `
        -LastAccessTime ($cutoffDate.AddDays(-70)) -CreationTime ($cutoffDate.AddDays(-80)) `
        -LastWriteTime ($cutoffDate.AddDays(-75)) -IsHidden $true
    
    # Large files
    $largeContent = 'A' * 1048576  # 1 MB of 'A's
    New-TestFile -Path $dir -Name "LargeFile1.bin" -Content $largeContent `
        -LastAccessTime ($cutoffDate.AddDays(-90)) -CreationTime ($cutoffDate.AddDays(-100)) `
        -LastWriteTime ($cutoffDate.AddDays(-95))
}

# List the generated files
Get-ChildItem -Path $testRootPath -Recurse -Force | Select-Object FullName, LastAccessTime, CreationTime, Attributes
