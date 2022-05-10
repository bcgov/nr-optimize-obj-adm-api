@ECHO OFF
:: This batch file disconnects the GeoDrive shares on this server, restarts the GeoDrive service, and then re-connects the shares. The purpose of this is to skip the recovery process for mapped GeoDrive shares prior to restarting the GeoDrive service.
TITLE GeoDrive Shares and Service Restart
START cloud_cli.exe disconnect
timeout /t 60 /nobreak > NUL
NET Stop "GDSvc" > NUL
timeout /t 10 /nobreak > NUL
NET Start "GDSvc" > NUL
timeout /t 300 /nobreak > NUL
cloud_cli.exe disconnect /off
EXIT 0