# -------------------------------------------------------------------------------
# Name:        sfp_objstor_robo.ps1
# Purpose:     Read folder and files from SFP and export a list of permissions 

# Parameters:
#   - RootOrigin is the SFP share, e.g. \\sfp.idir.bcgov\S161\S6202\
# Powershell usage:  ./sfp_objstor_robo.ps1 -RootOrigin <Origin Path>
# example: powershell ./save_sfp_permissions.ps1 -RootOrigin "E:\FOI_Litigation\WLRS FOI"
# 
# The script can also be run with the text output dumped to a text file:
# example: powershell ./sfp_objstor_robo.ps1 -RootOrigin "Z:\" *> "C:\Users\$($env:USERNAME)\permissions_output.txt"
# The output text file can be read as it is written to using a seperate powershell window to monitor progress:
# example: Get-Content "C:\Users\$($env:USERNAME)\historic_regional_mine_records.txt" -Wait
#
# Authors:      PPLATTEN
#
# Created:     2024-07-26
# Copyright:   (c) Optimization Team 2024
# Licence:     Open
# -------------------------------------------------------------------------------

param (
   [Parameter(Mandatory=$true)][string]$RootOrigin # top folder
)

Write-Host "RootOrigin: $($RootOrigin)"

$Output = @() # an array placeholder for the output csv
$SavePath = "C:\Users\$($env:USERNAME)" # Save location for the output file(s)
$SaveName = "permissions_$(Get-Date -format yyyy-MM-dd_HHmm)" # file name with dynamic timestamp
$excludepattern = 'nt authority\system', 'builtin\administrators', 'creator owner', 'builtin\users' # replace "-like $includepattern" with "-ne $excludepattern" if you want to list all groups/users except these ones

$AllOriginFolders = Get-ChildItem -Recurse -Directory -Path $RootOrigin
$AllOriginFolders += Get-Item -Path $RootOrigin
$AllFolderPaths = $AllOriginFolders | Select-Object FullName

ForEach ($FolderPath in $AllFolderPaths) {
    $FolderPath = $FolderPath.FullName
    Write-Host "ACLs for Folder: $($FolderPath)"

    $OriginAcl = Get-Acl -Path $FolderPath

    # Apply inherited permissions explicitly for the root directory ONLY   
    ForEach ($Access in $OriginAcl.Access | Where-Object {($_.identityreference -notin $excludepattern) -and ($_.IsInherited -EQ $True) -and ($($FolderPath) -EQ $($RootOrigin))}) { # filters folder ACL info to meet specifications 
        $Right = $Access.FileSystemRights
        Write-Host "$($Access.identityreference) ||| Right $($Right)"
        $fileSystemAccessRuleArgumentList = $Access.identityreference, $Access.FileSystemRights, $Access.InheritanceFlags, $Access.PropagationFlags, "Allow"
        $fileSystemAccessRule = New-Object -TypeName System.Security.AccessControl.FileSystemAccessRule -ArgumentList $fileSystemAccessRuleArgumentList
        $Properties = [ordered]@{'Origin Folder Name'=$($FolderPath); 'Type'='Folder';'Group/User'=$Access.IdentityReference;'Permissions'=$Access.FileSystemRights;'Inherited'=$Access.IsInherited;'InheritanceFlags'=$Access.InheritanceFlags;'ObjectInherit'=$Access.ObjectInherit} # puts desired ACL info into a tidy format
        $Output += New-Object -TypeName PSObject -Property $Properties # saves all the properties into an array
    }
    
    # Apply explicit permissions
    ForEach ($Access in $OriginAcl.Access | Where-Object {($_.identityreference -notin $excludepattern) -and ($_.IsInherited -EQ $False)}) { # filters folder ACL info to meet specifications 
        Write-Host "$($Access.identityreference) ||| Right $($Access.FileSystemRights)"
        $fileSystemAccessRuleArgumentList = $Access.identityreference, $Access.FileSystemRights, $Access.InheritanceFlags, $Access.PropagationFlags, "Allow"
        $fileSystemAccessRule = New-Object -TypeName System.Security.AccessControl.FileSystemAccessRule -ArgumentList $fileSystemAccessRuleArgumentList
        $Properties = [ordered]@{'Origin Folder Name'=$($FolderPath); 'Type'='Folder';'Group/User'=$Access.IdentityReference;'Permissions'=$Access.FileSystemRights;'Inherited'=$Access.IsInherited;'InheritanceFlags'=$Access.InheritanceFlags;'ObjectInherit'=$Access.ObjectInherit} # puts desired ACL info into a tidy format
        $Output += New-Object -TypeName PSObject -Property $Properties # saves all the properties into an array
    }    
    
}

Write-Host "Saving CSV"
$Output | export-csv -NoTypeInformation $SavePath\$SaveName.csv # saves the array to a CSV file and saves it to the location and file name specified