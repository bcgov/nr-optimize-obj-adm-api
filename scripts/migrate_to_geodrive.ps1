# VPN or wired ethernet connection to BCGOV network is required for this script to run properly
# OneDrive must be enabled on the workstation
# GeoDrive share must be accessible to the person running the script

$HDrive = "H:"
$OneDrive = "C:\Users\$($env:USERNAME)\OneDrive - Government of BC\"
$Logpath = "C:\Users\$($env:USERNAME)\OneDrive - Government of BC\Logs"
$date = "Migrate_to_GeoDrive_$(Get-Date -format yyyyMMdd-HHmm)"

$xd = "$RECYCLE.BIN, $HDrive\Profile", "$HDrive\WINDOWS", "$HDrive\CFGFiles", "$HDrive\DYMO", "$HDrive\DYMO Label", "$HDrive\TRIM", "$HDrive\TRIM Data", "$HDrive\My Received Files", "$HDrive\Remote Assistance Logs", "$HDrive\Documents", "$HDrive\Pictures", "$HDrive\Outlook Files", "$HDrive\Custom Office Templates", "*." # excluded directories
$xf = "*.pst", "*.cfg", "*_vti_*.*", "~$*.*", "*.lock", "*.ini", "*.tmp", "*.one", "*.gdb", "*.accdb", "*.mdb", "*.sql", "*.sqlite", "*.db", "*.db3" # excluded files

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

    Write-Host -ForegroundColor Cyan "`n`nThis script is intended to help move non-personal files from your chosen folder to a GeoDrive share (Object Storage). `nAs a precaution, your Profile folder and other default H Drive folders are automatically excluded from this data migration."  
    Write-Host "`nYou must have a connection to the BCGOV network and have OneDrive enabled/installed for the log file. Do you wish to proceed?" -NoNewline 
    $proceed = Write-Host " [y/n] " -ForegroundColor Yellow -NoNewline 
    $proceed = Read-Host
    Write-Host " `n "

    if ($proceed -eq 'y') {
        Do {
            $Source = Write-Host "Source pathname (where the data is now), including the drive letter or use full network path. If you encounter difficulties, try putting quotation marks around the entire path : " -NoNewline
            $Source = Read-Host
            Write-Host " `n "

            # Loop if Source Path check fails
            if (!(Test-Path -Path $Source)) {
                do {
                    Write-Host -ForegroundColor Red "Could not connect to $Source. Path may not exist, VPN might be disconnected, or security groups could be restricting access."
                    $Destination = Write-Host "Input pathname, including the drive letter or use full network path. If you encounter difficulties, try putting quotation marks around the entire path : " -NoNewline
                    $Destination = Read-Host
                    Write-Host " `n "    
                } until (Test-Path -Path $Source)
            }

            Write-Host "You input the path name '$Source'. Is this correct?" -NoNewline 
            $correct = Write-Host " [y/n] " -ForegroundColor Yellow -NoNewline 
            $correct = Read-Host
            Write-Host " `n " 
        }
        while ($correct -ne "y")


        Do {
            $Destination = Write-Host "Destination pathname, including the drive letter or use full network path. If you encounter difficulties, try putting quotation marks around the entire path : " -NoNewline
            $Destination = Read-Host
            Write-Host " `n "

            # Loop if Path check fails
            if (!(Test-Path -Path $Destination)) {
                do {
                    Write-Host -ForegroundColor Red "Could not connect to $Destination. Path may not exist, VPN might be disconnected, or security groups could be restricting access."
                    $Destination = Write-Host "Input pathname, including the drive letter or use full network path. If your pathname has spaces, put quotation marks around the entire path : " -NoNewline
                    $Destination = Read-Host
                    Write-Host " `n "    
                } until (Test-Path -Path $Destination)
            }
            
            Write-Host "You input the path name '$Destination'. Is this correct?" -NoNewline 
            $correct = Write-Host " [y/n] " -ForegroundColor Yellow -NoNewline 
            $correct = Read-Host
            Write-Host " `n " 
        }
        while ($correct -ne "y")

        Write-Host "Do you wish to exclude any additional folders within $Source from this migration?" -NoNewline
	    $addl_folders = Write-Host " [y/n] " -ForegroundColor Yellow -NoNewline
	    $addl_folders = Read-Host
	    Write-Host " `n "

        if ($addl_folders -eq 'y') {
            Write-Host "Enter folder pathname(s), including the drive letter or use full network path. Please use quotation marks and a space to separate each folder you are listing i.e ""H:\Folder1""" "" -NoNewline
            Write-Host """H:\Folder2\Personal""" ""  -NoNewline
            Write-Host """H:\Folder3\Resumes\Cover Letters"""
            $excl_folders = Write-Host "Folder Pathname(s): " -ForegroundColor Yellow -NoNewline
            $excl_folders = Read-Host 
            $xd = $xd += $excl_folders -split '\s+' # splits client input on empty space delimiter and appends it to the xd variable
            Write-Host " `n "
            do {
                Write-Host "You input these folder(s) to exclude: $excl_folders. Is this correct?" -NoNewline 
                $corr = Write-Host " [y/n] " -ForegroundColor Yellow -NoNewline 
                $corr = Read-Host
                Write-Host " `n "
                } until ($corr -eq "y")
            }

        Write-Host "Do you wish to exclude any additional files or filetype extensions within $Source from this migration?" -NoNewline
	    $addl_files = Write-Host " [y/n] " -ForegroundColor Yellow -NoNewline
	    $addl_files = Read-Host
	    Write-Host " `n "

        if ($addl_files -eq 'y') {
            Write-Host "Enter file name(s) and/or *.extension to exclude all files with a particular extension. Please use quotation marks and a space to separate each file or filetype you are listing i.e ""myfile.txt""" "" -NoNewline
            Write-Host """*.pdf""" ""  -NoNewline
            Write-Host """*.shp"""
            $excl_files = Write-Host "Folder Pathname(s): " -ForegroundColor Yellow -NoNewline
            $excl_files = Read-Host 
            $xf = $xf += $excl_files -split '\s+' # splits client input on empty space delimiter and appends it to the xf variable
            Write-Host " `n "

            do {
                Write-Host "You input these files(s) and/or filetype extensions to exclude: $excl_files. Is this correct?" -NoNewline 
                $corrxf = Write-Host " [y/n] " -ForegroundColor Yellow -NoNewline 
                $corrxf = Read-Host
                Write-Host " `n "
                } until ($corrxf -eq "y")
        }

        Write-Host "Choose " -NoNewline 
        Write-Host "y " -ForegroundColor Yellow -NoNewline 
        Write-Host "if you wish to remove your data from $Source once it has been copied to $Destination, or " -NoNewline 
        Write-Host "n " -ForegroundColor Yellow -NoNewline 
        Write-Host "if you intend to manually delete the data from $Source at a later time." -NoNewline
        $removedata = Write-Host " [y/n] " -ForegroundColor Yellow -NoNewline 
        $removedata = Read-Host
        Write-Host " `n "
    }

    if ($removedata -eq 'n') {
        Write-Host "Your files will be copied to $Destination. As a precaution, Outlook archive files as well as GeoDatabase files & folders will NOT be copied over." -ForegroundColor Red 
        Write-Host -ForegroundColor DarkCyan "`nCopying Data to $Destination. This may take several minutes..."
        robocopy $Source $Destination /V /NP /log+:$logpath\log-$date.txt /S /Z /R:1 /W:1 /MT:64 /XA:SH /XF $xf /XD $xd  
        if ($lastexitcode -gt 1) { 
            Write-Host "Robocopy exit code:" $lastexitcode 
        }
        else { 
            Write-Host -BackgroundColor Yellow "Your contents on $Source have been copied to the specified $Destination share. `nVerify the copy was successful, then review $Source and manually remove any data already available in $Destination at your earliest convenience. `n Please remember to empty your recycling bin following the cleanup" -NoNewline 
        }
    }
    elseif ($removedata -eq 'y') {
        Write-Host "Your files will be moved to $Destination. As a precaution, Outlook archive files as well as GeoDatabase files & folders will NOT be moved." -ForegroundColor Red 
        Write-Host -ForegroundColor DarkCyan "`nMoving Data to $Destination. This may take several minutes..."
        robocopy /MOVE /S /Z $Source $Destination /V /NP /log+:$logpath\log-$date.txt /R:1 /W:1 /MT:64 /XA:SH /XF $xf /XD $xd  
        if ($LastExitCode -gt 1) {
            Write-Host "Robocopy exit code:" $lastexitcode
        }
        else {
            Write-Host -BackgroundColor Yellow "Your contents on $Source have been moved to $Destination. Thank you!"
        }
    }

    Else { "Please enable OneDrive before running this script" }

    # If running in the console, wait for input before closing.
    if ($Host.Name -eq "ConsoleHost") {
        Write-Host "Press any key to continue..."
        $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyUp") > $null
    }
}