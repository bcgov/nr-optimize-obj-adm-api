# Robocopy to create empty folders
# - (If we copy everything then apply permissions it needs to change permissions on each already copied file. If we do folders first inherited permissions are added for free when we copy a file)
# For Each Folder: 
# Folder ACLs
# If destination root folder, Apply folder ACLs to the directory where ACLs were inherited on the origin and where inheritance is ContainerInherit.
# - (ContainerInherit is whether or not a permission will be inherited by a folders children. So these are ACLs that were inherited and also will be inherited)
# If destination root folder, Apply folder ACLs to the top-level directory where ACLs were inheritedon the origin and where inheritance is not ContainerInherit
# - (This can overwrite ListDirectory where applicable. If we did these first some users would only have ListDirectory when they should have read, execute, and listdirectory.)
# Apply non-inherited folder ACLs where inheritance is ContainerInherit
# - (This causes the ACLs explicitly declared on the folder to overwrite ones inherited from up the tree from the origin directory)
# Apply non-inherited folder ACLs where inheritance is not ContainerInherit 
# - (this will overwrite ListDirectory where applicable)
# For each file:
# Robocopy File
# Get file ACLs
# Apply non-inherited file ACLs 
