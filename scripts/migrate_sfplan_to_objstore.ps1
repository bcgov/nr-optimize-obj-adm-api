# VPN connection is required for this script to run properly
# OneDrive must be enabled on the workstation
# GeoDrive share must be mapped on the workstation

$SFPLAN = "<path to SFP, LAN, or SAN folder>"
$GeoDrive = "<path to mapped GeoDrive Share>"
$xf_ext = Get-Content C:\Git_Repo\nr-optimize-obj-adm-api\scripts\exclude_extensions.txt
$OneDrive = "C:\Users\$($env:USERNAME)\OneDrive - Government of BC\"
$Logpath = "C:\Users\$($env:USERNAME)\OneDrive - Government of BC\Logs"
$date = "Object_Storage_Migration_$(Get-Date -format yyyyMMddHHmm)"

if (Test-Path -Path $OneDrive) {

    # Create folder if does not exist
    if (!(Test-Path -Path $Logpath)) {
        $paramNewItem = @{
            Path     = $Logpath
            ItemType = 'Directory'
            Force    = $true
        }

        New-Item @paramNewItem
    }

    Write-Host "`nThis script is intended to help copy files from your SFP, LAN, or SAN share to ObjectStorage. It is assumed you have read & understood the information on this service at https://apps.nrs.gov.bc.ca/int/confluence/display/OPTIMIZE/SFP+Reduction+Strategies"  
    Write-Host "You must have a VPN connection and have OneDrive enabled/installed for the log file. Do you wish to proceed?" -NoNewline 
    $confirmationcopy = Write-Host " [y/n] " -ForegroundColor Yellow -NoNewline 
    $confirmationcopy = Read-Host

    if ($confirmationcopy -eq 'y') {
        Write-Host "Choose " -NoNewline 
        Write-Host "y " -ForegroundColor Yellow -NoNewline 
        Write-Host "if you wish to remove your data from the SFP, LAN, or SAN share once it has been copied to ObjectStorage, or " -NoNewline 
        Write-Host "n " -ForegroundColor Yellow -NoNewline 
        Write-Host "if you intend to manually delete the data from the SFP, LAN, or SAN share at a later time." -NoNewline
        $removedata = Write-Host " [y/n] " -ForegroundColor Yellow -NoNewline
        $removedata = Read-Host

        Write-Host "It is strongly advised that you do not move ACTIVE database (.gdb, .mdb) or .pst files to Object Storage. Over time, these files can become corrupted." -ForegroundColor Red
        Write-Host "If you have database and/or .pst files, are you sure you want to move them from the SFP, LAN, or SAN share to Object Storage?"  -NoNewline
        $XfConfirm = Write-Host " [y/n] " -ForegroundColor Yellow -NoNewline
        $XfConfirm = Read-Host
    }

    if ($XfConfirm -eq 'y' -and ($removedata -eq 'n')) {
        Write-Host "Your database and .pst files will be moved to Object Storage. Please ensure any associated Outlook folders have been closed before proceeding." -ForegroundColor Red 
        Write-Host -ForegroundColor White -BackgroundColor Blue "`nCopying Data to Object Storage. This may take a few minutes..."
        robocopy $SFPLAN $GeoDrive /V /NP /log+:$logpath\log-$date.txt /E /Z /R:1 /W:1 /MT:32   
        if ($lastexitcode -gt 1) { 
            Write-Host "Robocopy exit code:" $lastexitcode 
        }
        else { 
            Write-Host -ForegroundColor Blue "Your SFP, LAN, or SAN share contents have been copied to Object Storage. Verify the copy was successful, then review your SFP, LAN, or SAN share and manually remove any data already available in Object Storage at your earliest convenience. `n Please remember to empty your recycling bin following the cleanup" -NoNewline 
        }
    }
    elseif ($XfConfirm -eq 'n' -and ($removedata -eq 'n')) {
        Write-Host "Your database and .pst files will remain on the SFP, LAN, or SAN share" -ForegroundColor Yellow
        Write-Host -ForegroundColor Blue "`nCopying Data to Object Storage. This may take a few minutes..."
        robocopy $SFPLAN $GeoDrive /V /NP /log+:$logpath\log-$date.txt /E /Z /R:1 /W:1 /MT:32 /xf $xf_ext  
        if ($lastexitcode -gt 1) { 
            Write-Host "Robocopy exit code:" $lastexitcode 
        }
        else { 
            Write-Host -ForegroundColor White -BackgroundColor DarkBlue "Your SFP, LAN, or SAN share contents have been copied to Object Storage. Verify the copy was successful, then review your SFP, LAN, or SAN share and manually remove any data already available in Object Storage at your earliest convenience. `n Please remember to empty your recycling bin following the cleanup" -NoNewline 
        }
    }
    elseif ($XfConfirm -eq 'y' -and ($removedata -eq 'y')) {
        Write-Host "Your database and .pst files will be moved to Object Storage. Please ensure any associated Outlook folders have been closed before proceeding." -ForegroundColor Red 
        Write-Host -ForegroundColor Blue "`nCopying Data to Object Storage. This may take a few minutes..."
        robocopy /MOVE /E /Z $SFPLAN $GeoDrive /V /NP /log+:$logpath\log-$date.txt /R:1 /W:1 /MT:32   
        if ($LastExitCode -gt 1) {
            Write-Host "Robocopy exit code:" $lastexitcode
        }
        else {
            Write-Host -ForegroundColor White -BackgroundColor DarkBlue "Your SFP, LAN, or SAN share contents have been moved to Object Storage. Thank you!"
        }
    }
    elseif ($XfConfirm -eq 'n' -and ($removedata -eq 'y')) {
        Write-Host "Your database and .pst files will remain on the SFP, LAN, or SAN share" -ForegroundColor Yellow
        Write-Host -ForegroundColor Blue "`nCopying Data to Object Storage. This may take a few minutes...`n"
        robocopy /MOVE /E /Z $SFPLAN $GeoDrive /V /NP /log+:$logpath\log-$date.txt /R:1 /W:1 /MT:32 /xf $xf_ext  
        if ($LastExitCode -gt 1) {
            Write-Host "Robocopy exit code:" $lastexitcode
        }
        else {
            Write-Host -ForegroundColor White -BackgroundColor DarkBlue "Your SFP, LAN, or SAN share contents have been moved to Object Storage. Thank you!"
        }
    }


    Else { "Please enable OneDrive before running this script" }

    # If running in the console, wait for input before closing.
    if ($Host.Name -eq "ConsoleHost") {
        Write-Host "Press any key to continue..."
        $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyUp") > $null
    }
}