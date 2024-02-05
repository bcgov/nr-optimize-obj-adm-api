# -------------------------------------------------------------------------------
# Name:        sfp_objstor_robo.ps1
# Purpose:     the purpose of the script is to create a folder hierachy in GeoDrive 
#              that matches the client's existing SFP structure, THEN apply ACLs, THEN copy the files into the folders.
#              1.) For each folder:
#		        a.) If destination is a root folder, apply folder ACLs to the directory 
#                   where the ACLs were inherited on the origin and where inheritance IS ContainerInherit.
#               b.) If destination is a root folder, apply folder ACLs to the directory 
#                   where the ACLs were inherited on the origin and where inheritance IS NOT ContainerInherit.
#               c.) Apply non-inherited folder ACLs where inheritance IS  ContainerInherit
#               d.) Apply non-inherited folder ACLs where inheritance IS NOT ContainerInherit
#              2.) For each file:
#               a.) Robocopy file
#               b.) Get file ACLs
#               c.) Apply non-inheirited file ACLs where inheritance IS ContainerInherit
#               d.) Apply non-inheirited file ACLs where inheritance IS NOT ContainerInherit
# Notes:	ContainerInherit is whether or not a permission will be inherited by a folder's children.
#
# Author:      PPLATTEN, HHAY
#
# Created:     2024-01-31
# Copyright:   (c) Optimization Team 2024
# Licence:     mine
#
#
# usage: powershell ./sfp_objstor_robo.ps1
# example: powershell ./sfp_objstor_robo.ps1
# -------------------------------------------------------------------------------

param (
    [Parameter(Mandatory=$true)][string]$RootOrigin, # copy from location
    [Parameter(Mandatory=$true)][string]$RootDestination # to location
 )

$Output = @() # an array placeholder for the output csv
$SavePath = "C:\Users\$($env:USERNAME)" # Save location for the output file(s)
$SaveName = "permissions_to_apply_$(Get-Date -format yyyy-MM-dd_HHmm)" # file name with dynamic timestamp
$excludepattern = 'nt authority\system', 'builtin\administrators', 'creator owner', 'builtin\users' # replace "-like $includepattern" with "-ne $excludepattern" if you want to list all groups/users except these ones
$includepattern = '*_*' # a workaround to list security groups instead of individual IDIRS, it only selects groups/users with an underscore in the name. It still captures _A accounts

$AllOriginFolders = Get-ChildItem -Recurse -Directory -Path $RootOrigin
$AllOriginFolders += Get-Item -Path $RootOrigin
$AllFolderPaths = $AllOriginFolders | Select-Object FullName
ForEach ($FolderPath in $AllFolderPaths) {
    Write-Host "Starting $FolderPath"
    $OriginAcl = Get-Acl -Path $FolderPath
    ForEach ($Access in $OriginAcl.Access | Where-Object identityreference -notin $excludepattern) { # filters folder ACL info to meet specifications 
        $Right = $Access.FileSystemRights
        Write-Host "Starting $($Right) $($Access.identityreference)"
    }
}
Exit

$InheritanceFlag = [System.Security.AccessControl.InheritanceFlags]::ContainerInherit -bor [System.Security.AccessControl.InheritanceFlags]::ObjectInherit
$PropagationFlag = [System.Security.AccessControl.PropagationFlags]::None

$OriginAcl = Get-Acl -Path $RootOrigin # Gets ACL information for the folders
$RootAllowIdentities = @{}
ForEach ($Access in $OriginAcl.Access | where identityreference -notin $excludepattern) { # filters folder ACL info to meet specifications 
    $Right = $Access.FileSystemRights
    Write-Host "Starting $($Right) $($Access.identityreference)"
    If (-not ($RootAllowIdentities.Keys -contains $Access.identityreference.value)) {
        Write-Host "New Allow Hashtable for $($Access.identityreference.value)"
        $RootAllowIdentities[$Access.identityreference.value] = New-Object System.Collections.Generic.List[System.Object]
    }
    # Handle an odd issue where Get-Acl will show ListDirectory as ReadAndExecute
    $inheritanceFlg = $Access.InheritanceFlags.ToString();
    Write-Host $Right
    If ($Right.ToString() -like '*ReadAndExecute*') {
        Write-Host "ReadAndExecute like $($Right)"
        If ($inheritanceFlg -eq 'ContainerInherit') {
            Write-Host $inheritanceFlg
            $Right = $Right.ToString().replace('ReadAndExecute','ListDirectory, ReadAttributes, ReadExtendedAttributes, ReadPermissions, Traverse');
        }
    }
    If (-not ($RootAllowIdentities[$Access.identityreference.value] -contains $Right)) {
        Write-Host "New Allow right for User: $($Access.IdentityReference) $($Right)"
        $RootAllowIdentities[$Access.identityreference.value].Add($Right)
    }
}

ForEach ($RootAllowIdentity in $RootAllowIdentities.Keys) {
    Write-Host "Applying Folder Root Permissions For $($RootAllowIdentity)"
    ForEach($Right in $RootAllowIdentities[$RootAllowIdentity]) {
        Write-Host "Right: $($Right)"        
    }
    $Joined = $RootAllowIdentities[$RootAllowIdentity] -join ","
    Write-Host "Joined: $($Joined)"
    $Rights = [System.Security.AccessControl.FileSystemRights] $Joined
    Write-Host "Rights: $($Rights)"

    # Create new rule
    $DestinationAcl = Get-Acl -Path $RootDestination
    $fileSystemAccessRuleArgumentList = $RootAllowIdentity, $Rights, $InheritanceFlag, $PropagationFlag, "Allow"
    $fileSystemAccessRule = New-Object -TypeName System.Security.AccessControl.FileSystemAccessRule -ArgumentList $fileSystemAccessRuleArgumentList
    # Apply new rule
    $DestinationAcl.SetAccessRule($fileSystemAccessRule)
    Set-Acl -Path $RootDestination -AclObject $DestinationAcl
     
    Write-Host "Ending Root Folder Permission Copy"
    Write-Host "Adding changes to Output"
    $Properties = [ordered]@{'Origin Folder Name'=$RootOrigin; 'Destination Folder Name'=$RootDestination;'Group/User'=$Access.IdentityReference;'Permissions'=$Access.FileSystemRights;'Inherited'=$Access.IsInherited} # puts desired ACL info into a tidy format
    $Output += New-Object -TypeName PSObject -Property $Properties # saves all the requested drive/folderpath/folder/AC info into an array
}


Write-Host "Saving CSV"
$Output | export-csv -NoTypeInformation $SavePath\$SaveName.csv # saves the array to a CSV file and saves it to the location and file name specified

Exit

$FolderPath = Get-ChildItem -Path $RootOrigin -Recurse # Gets each folder path in each drive, to a folder hierarchy depth of 3
ForEach ($Folder in $FolderPath) { # Looks into every folder in the folder path list 
    $Acl = Get-Acl -Path $Folder.FullName # Gets ACL information for the folders
    ForEach ($Access in $Acl.Access | where identityreference -notin $excludepattern | where IsInherited -NE TRUE) { # filters folder ACL info to meet specifications 
        Write-Host "Starting Folder Permission Copy for "+$Folder.FullName.Replace($RootOrigin,$RootDestination)
        Write-Host "User: "+$Access.IdentityReference
        $Properties = [ordered]@{'Origin Folder Name'=$Folder.FullName; 'Destination Folder Name'=$Folder.FullName.Replace($RootOrigin,$RootDestination);'Group/User'=$Access.IdentityReference;'Permissions'=$Access.FileSystemRights;'Inherited'=$Access.IsInherited} # puts desired ACL info into a tidy format
        
        Write-Host "Adding changes to Output"
        $Output += New-Object -TypeName PSObject -Property $Properties # saves all the requested drive/folderpath/folder/AC info into an array
    }
}
