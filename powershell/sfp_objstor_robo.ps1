# -------------------------------------------------------------------------------
# Name:        sfp_objstor_robo.ps1
# Purpose:     Copy files from SFP to GeoDrive maintaining permissions
# Steps:
# 1. Handle Folders first (This makes it so that inherited permissions are already on the folder when files are added, 
# and files do not need to be updated for access.)
#   1a. Robocopy Folders Without Permissions
#   1b. Copy inherited permissions on root origin directory as explicit permissions on destination root directory
#   1c. Copy explicit permissions on all origin directories as explicit permissions on all destination directories
#   1d. Copy ownership of all directories (Note: Once copied, the owner will have an extra permissions entry as well as being the owner)  
# 2. Handle Files
#   2a. Robocopy Files Without Permissions
#   2b. Copy explicit permissions for all files
#   2c. Copy ownership for all files.
#
# Notes:	
#   - Excludepattern ensures permissions specific to SFP are skipped
#   - Script must be run from the destination server, with at least read access on the origin. Testing has only been done with Full Access to origin.
#     - If origin access is tied to a different credential-set than the destination server, 
#       the following powershell command can be used to map a network drive with the credentials:
#       net use "\\sfp.idir.bcgov\S161" "Z:" /user:IDIR\pplatten ThePassword
#       Note that this command will not mask ThePassword in the console.
#
# Parameters:
#   - RootOrigin is the SFP share, e.g. \\sfp.idir.bcgov\S161\S6202\
#   - RootDestination is the GeoDrive share, e.g. \\objectstore.nrs.bcgov\nrs-iit\S6202\
# Powershell usage:  ./sfp_objstor_robo.ps1 -RootOrigin <Origin Path> -RootDestination <Destination Path>
# example: powershell ./sfp_objstor_robo.ps1 -RootOrigin "\\sfp.idir.bcgov\S161\S6202\Mines Operations\Regional Operations\File Digitization Project - Pilot" -RootDestination "\\objectstore.nrs.bcgov\nrs-iit\icacls_testing\"
#
# Authors:      PPLATTEN, HHAY
#
# Created:     2024-01-31
# Copyright:   (c) Optimization Team 2024
# Licence:     Open
# -------------------------------------------------------------------------------

# param (
#    [Parameter(Mandatory=$true)][string]$RootOrigin, # copy from location
#    [Parameter(Mandatory=$true)][string]$RootDestination # to location
# )

$RootOrigin = "Z:\!RUSH\"
$RootDestination = "E:\GeoDriveCache\nrs-iit\icacls_testing\!RUSH\"

Write-Host "RootOrigin: $($RootOrigin)"
Write-Host "RootDestination: $($RootDestination)"

$Output = @() # an array placeholder for the output csv
$SavePath = "C:\Users\$($env:USERNAME)" # Save location for the output file(s)
$SaveName = "permissions_to_apply_$(Get-Date -format yyyy-MM-dd_HHmm)" # file name with dynamic timestamp
$excludepattern = 'nt authority\system', 'builtin\administrators', 'creator owner', 'builtin\users' # replace "-like $includepattern" with "-ne $excludepattern" if you want to list all groups/users except these ones

# Robocopy empty folders:
robocopy $RootOrigin $RootDestination /e /nocopy

$AllOriginFolders = Get-ChildItem -Recurse -Directory -Path $RootOrigin
$AllOriginFolders += Get-Item -Path $RootOrigin
$AllFolderPaths = $AllOriginFolders | Select-Object FullName

ForEach ($FolderPath in $AllFolderPaths) {
    $FolderPath = $FolderPath.FullName
    Write-Host "ACLs for Folder: $($FolderPath)"
    # Handle copying from root of a mapped drive (i.e. Z:\ rather than Z:\foldername )
    If ($RootOrigin.EndsWith("\") -or $RootDestination.StartsWith("\")) {
        $Destination = $FolderPath.Replace($RootOrigin,$RootDestination)
    }else {
        $Destination = $FolderPath.Replace($RootOrigin,$RootDestination + "\")
    }
    $OriginAcl = Get-Acl -Path $FolderPath
    $DestinationAcl = Get-Acl -Path $Destination

    # Apply inherited permissions explicitly for the root directory ONLY   
    ForEach ($Access in $OriginAcl.Access | Where-Object {($_.identityreference -notin $excludepattern) -and (($_.IsInherited -EQ $True) -and ($Destination -eq $RootDestination))}) { # filters folder ACL info to meet specifications 
        $Right = $Access.FileSystemRights
        Write-Host "$($Access.identityreference) ||| Right $($Right)"
        $fileSystemAccessRuleArgumentList = $Access.identityreference, $Access.FileSystemRights, $Access.InheritanceFlags, $Access.PropagationFlags, "Allow"
        $fileSystemAccessRule = New-Object -TypeName System.Security.AccessControl.FileSystemAccessRule -ArgumentList $fileSystemAccessRuleArgumentList
        # Apply new rule
        $DestinationAcl.AddAccessRule($fileSystemAccessRule)
        $Properties = [ordered]@{'Origin Folder Name'=$Folder.FullName; 'Destination Folder Name'=$Destination;'Type'='Folder';'Group/User'=$Access.IdentityReference;'Permissions'=$Access.FileSystemRights;'Inherited'=$Access.IsInherited;'InheritanceFlags'=$Access.InheritanceFlags;'ObjectInherit'=$Access.ObjectInherit} # puts desired ACL info into a tidy format
        $Output += New-Object -TypeName PSObject -Property $Properties # saves all the properties into an array
    }
    
    # Apply explicit permissions
    ForEach ($Access in $OriginAcl.Access | Where-Object {($_.identityreference -notin $excludepattern) -and ($_.IsInherited -EQ $False)}) { # filters folder ACL info to meet specifications 
        $Right = $Access.FileSystemRights
        Write-Host "$($Access.identityreference) ||| Right $($Right)"
        $fileSystemAccessRuleArgumentList = $Access.identityreference, $Access.FileSystemRights, $Access.InheritanceFlags, $Access.PropagationFlags, "Allow"
        $fileSystemAccessRule = New-Object -TypeName System.Security.AccessControl.FileSystemAccessRule -ArgumentList $fileSystemAccessRuleArgumentList
        # Apply new rule
        $DestinationAcl.AddAccessRule($fileSystemAccessRule)
        $Properties = [ordered]@{'Origin Folder Name'=$Folder.FullName; 'Destination Folder Name'=$Destination;'Type'='Folder';'Group/User'=$Access.IdentityReference;'Permissions'=$Access.FileSystemRights;'Inherited'=$Access.IsInherited;'InheritanceFlags'=$Access.InheritanceFlags;'ObjectInherit'=$Access.ObjectInherit} # puts desired ACL info into a tidy format
        $Output += New-Object -TypeName PSObject -Property $Properties # saves all the properties into an array
    }    
    $Owner = New-Object -TypeName System.Security.Principal.NTAccount -ArgumentList $OriginAcl.Owner;
    # $DestinationAcl.SetOwner($Owner)
    Set-Acl -Path $Destination -AclObject $DestinationAcl
    
}

# Copy Files
robocopy $RootOrigin $RootDestination /e /j /v /eta /np /copy:DAT /nodcopy

# Apply permissions, one folder at a time
ForEach ($FolderPath in $AllFolderPaths) {
    # Get and Apply permissions
    $Files = Get-ChildItem -Path $FolderPath.FullName -File
    ForEach ($File in $Files){
        $FilePath = $File.FullName
        Write-Host "ACLs for File: $($FilePath)"
        # Handle copying from root of a mapped drive (i.e. Z:\ rather than Z:\foldername )
        If ($RootOrigin.EndsWith("\\") -or $RootDestination.StartsWith("\\")) {
            $Destination = $FilePath.Replace($RootOrigin,$RootDestination)
        }else {
            $Destination = $FilePath.Replace($RootOrigin,$RootDestination + "\")
        }        
        $OriginAcl = Get-Acl -Path $FilePath
        $DestinationAcl = Get-Acl -Path $Destination
        # Apply explicit permissions
        ForEach ($Access in $OriginAcl.Access | Where-Object {($_.identityreference -notin $excludepattern) -and ($_.IsInherited -EQ $False)}) { # filters folder ACL info to meet specifications 
            $Right = $Access.FileSystemRights
            Write-Host "$($Access.identityreference) ||| Right $($Right)"
            $fileSystemAccessRuleArgumentList = $Access.identityreference, $Access.FileSystemRights, $Access.InheritanceFlags, $Access.PropagationFlags, "Allow"
            $fileSystemAccessRule = New-Object -TypeName System.Security.AccessControl.FileSystemAccessRule -ArgumentList $fileSystemAccessRuleArgumentList
            # Apply new rule
            $DestinationAcl.AddAccessRule($fileSystemAccessRule)
            $Properties = [ordered]@{'Origin Folder Name'=$Folder.FullName; 'Destination Folder Name'=$Destination;'Type'='File';'Group/User'=$Access.IdentityReference;'Permissions'=$Access.FileSystemRights;'Inherited'=$Access.IsInherited;'InheritanceFlags'=$Access.InheritanceFlags;'ObjectInherit'=$Access.ObjectInherit} # puts desired ACL info into a tidy format
            $Output += New-Object -TypeName PSObject -Property $Properties # saves all the properties into an array
        }
        $Owner = New-Object -TypeName System.Security.Principal.NTAccount -ArgumentList $OriginAcl.Owner;
        # $DestinationAcl.SetOwner($Owner)
        Set-Acl -Path $Destination -AclObject $DestinationAcl
    }
}
Write-Host "Saving CSV"
$Output | export-csv -NoTypeInformation $SavePath\$SaveName.csv # saves the array to a CSV file and saves it to the location and file name specified