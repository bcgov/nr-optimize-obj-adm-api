@echo Create new drive mapping
@echo ------------------------
@echo off

:: User enters IDIR password which is hidden from view 
set "psCommand=powershell -Command "$pword = read-host 'Enter IDIR Password' -AsSecureString ; ^
      $BSTR=[System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($pword); ^
            [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)""
 for /f "usebackq delims=" %%p in (`%psCommand%`) do set password=%%p

:: User enters the absolute path for the folder they want mapped
set /p abspath="Enter full folder path you wish to map: " @pause

:: User chooses the drive letter they want the folder mapped to
set /p driveletter="Enter the drive letter (A to Z) you want to use: " @pause 

@echo Attempting to map drive letter %driveletter% to %abspath% ...

:: The folder path is now mapped to the specified drive letter using client credentials
@net use %driveletter%: "%abspath%" /USER:%username% %password% /persistent:Yes

:exit
@pause

