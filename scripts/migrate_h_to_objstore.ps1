# VPN connection is required for this script to run properly
# OneDrive must be enabled on the workstation
# GeoDrive share must be mapped on the workstation

$HDrive = "H:"
$GeoDrive = "<path to mapped GeoDrive Share>"
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

    Write-Host "`nThis script is intended to help copy non-personal files from your H: to ObjectStorage. Your Profile folder and others identified as needing to stay on the H Drive are automatically excluded from this move."  
    Write-Host "You must have a VPN connection and have OneDrive enabled/installed for the log file. Do you wish to proceed?" -NoNewline 
    $confirmationcopy = Write-Host " [y/n] " -ForegroundColor Yellow -NoNewline 
    $confirmationcopy = Read-Host

    if ($confirmationcopy -eq 'y') {
        Write-Host "Choose " -NoNewline 
        Write-Host "y " -ForegroundColor Yellow -NoNewline 
        Write-Host "if you wish to remove your data from the H: drive once it has been copied to ObjectStorage, or " -NoNewline 
        Write-Host "n " -ForegroundColor Yellow -NoNewline 
        Write-Host "if you intend to manually delete the data from H: at a later time." -NoNewline
        $removedata = Write-Host " [y/n] " -ForegroundColor Yellow -NoNewline
        $removedata = Read-Host

        Write-Host "It is strongly advised that you do not move ACTIVE .gdb or .pst files to Object Storage. Over time, these files can become corrupted." -ForegroundColor Red
        Write-Host "If you have .gdb and .pst files, are you sure you want to move them from H: to Object Storage?"  -NoNewline
        $PstConfirm = Write-Host " [y/n] " -ForegroundColor Yellow -NoNewline
        $PstConfirm = Read-Host
    }

    if ($PstConfirm -eq 'y' -and ($removedata -eq 'n')) {
        Write-Host "Your .gdb and .pst files will be moved to Object Storage. Please ensure any associated Outlook folders have been closed before proceeding. If you need help, refer to https://intranet.gov.bc.ca/nrids/onedrive/onedrive-faq" -ForegroundColor Red 
        Write-Host -ForegroundColor White -BackgroundColor Blue "`nCopying Data to Object Storage. This may take a few minutes..."
        robocopy $HDrive $GeoDrive /V /NP /log+:$logpath\log-$date.txt /E /Z /R:1 /W:1 /MT:32 /xf *.cfg *.ini *.one /xd "$HDrive\Profile" "$HDrive\WINDOWS" "$HDrive\CFGFiles" "$HDrive\DYMO" "$HDrive\DYMO Label" "$HDrive\TRIM" "$HDrive\TRIM Data" "$HDrive\My Received Files" "$HDrive\Remote Assistance Logs"  
        if ($lastexitcode -gt 1) { 
            Write-Host "Robocopy exit code:" $lastexitcode 
        }
        else { 
            Write-Host -ForegroundColor Blue "Your H: drive contents have been copied to Object Storage. Verify the copy was successful, then review your H: Drive and manually remove any data already available in Object Storage at your earliest convenience. `n Please remember to empty your recycling bin following the cleanup" -NoNewline 
        }
    }
    elseif ($PstConfirm -eq 'n' -and ($removedata -eq 'n')) {
        Write-Host "Your .pst and .gdb files will remain on the H: drive" -ForegroundColor Yellow
        Write-Host -ForegroundColor Blue "`nCopying Data to Object Storage. This may take a few minutes..."
        robocopy $HDrive $GeoDrive /V /NP /log+:$logpath\log-$date.txt /E /Z /R:1 /W:1 /MT:32 /xf *.cfg *.ini *.one *.pst *.gdb /xd "$HDrive\Profile" "$HDrive\WINDOWS" "$HDrive\CFGFiles" "$HDrive\DYMO" "$HDrive\DYMO Label" "$HDrive\TRIM" "$HDrive\TRIM Data" "$HDrive\My Received Files" "$HDrive\Remote Assistance Logs"  
        if ($lastexitcode -gt 1) { 
            Write-Host "Robocopy exit code:" $lastexitcode 
        }
        else { 
            Write-Host -ForegroundColor White -BackgroundColor DarkBlue "Your H: drive contents have been copied to Object Storage. Verify the copy was successful, then review your H: Drive and manually remove any data already available in OneDrive at your earliest convenience. `n Please remember to empty your recycling bin following the cleanup" -NoNewline 
        }
    }
    elseif ($PstConfirm -eq 'y' -and ($removedata -eq 'y')) {
        Write-Host "Your .gdb and .pst files will be moved to Object Storage. Please ensure any associated Outlook folders have been closed before proceeding. If you need help, refer to https://intranet.gov.bc.ca/nrids/onedrive/onedrive-faq" -ForegroundColor Red 
        Write-Host -ForegroundColor Blue "`nCopying Data to Object Storage. This may take a few minutes..."
        robocopy /MOVE /E /Z $HDrive $GeoDrive /V /NP /log+:$logpath\log-$date.txt /R:1 /W:1 /MT:32 /xf *.cfg *.ini *.one /xd "$HDrive\Profile" "$HDrive\WINDOWS" "$HDrive\CFGFiles" "$HDrive\DYMO" "$HDrive\DYMO Label" "$HDrive\TRIM" "$HDrive\TRIM Data" "$HDrive\My Received Files" "$HDrive\Remote Assistance Logs"  
        if ($LastExitCode -gt 1) {
            Write-Host "Robocopy exit code:" $lastexitcode
        }
        else {
            Write-Host -ForegroundColor White -BackgroundColor DarkBlue "Your H: drive contents have been moved to Object Storage. Thank you!"
        }
    }
    elseif ($PstConfirm -eq 'n' -and ($removedata -eq 'y')) {
        Write-Host "Your .gdb and .pst files will remain on the H: drive" -ForegroundColor Yellow
        Write-Host -ForegroundColor Blue "`nCopying Data to Object Storage. This may take a few minutes...`n"
        robocopy /MOVE /E /Z $HDrive $GeoDrive /V /NP /log+:$logpath\log-$date.txt /R:1 /W:1 /MT:32 /xf *.cfg *.ini *.one *.pst *.gdb /xd "$HDrive\Profile" "$HDrive\WINDOWS" "$HDrive\CFGFiles" "$HDrive\DYMO" "$HDrive\DYMO Label" "$HDrive\TRIM" "$HDrive\TRIM Data" "$HDrive\My Received Files" "$HDrive\Remote Assistance Logs"  
        if ($LastExitCode -gt 1) {
            Write-Host "Robocopy exit code:" $lastexitcode
        }
        else {
            Write-Host -ForegroundColor White -BackgroundColor DarkBlue "Your H: drive contents have been moved to Object Storage. Thank you!"
        }
    }


    Else { "Please enable OneDrive before running this script" }

    # If running in the console, wait for input before closing.
    if ($Host.Name -eq "ConsoleHost") {
        Write-Host "Press any key to continue..."
        $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyUp") > $null
    }
}