# -------------------------------------------------------------------------------
# Name:        sfp_objstor_robo.ps1
# Purpose:     the purpose of the script is to create a folder hierachy in GeoDrive that matches the client's existing SFP structure, THEN apply ACLs, THEN copy the files into the folders.
#              1.) For each folder:
#		        a.) If destination is a root folder, apply folder ACLs to the directory where the ACLs were inherited on the origin and where inheritance IS ContainerInherit.
#               b.)If destination is a root folder, apply folder ACLs to the directory where the ACLs were inherited on the origin and where inheritance IS NOT ContainerInherit.
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
