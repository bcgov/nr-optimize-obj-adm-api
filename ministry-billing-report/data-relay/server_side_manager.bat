


REM Run using: server_side_manager.bat SA_KEY CLUSTER_URL OBJSTOR_ADMIN OBJSTOR_PASS
REM SA_KEY is the service account key from OpenShift.
REM CLUSTER_URL is https://api.silver.devops.gov.bc.ca:6443
REM OBJSTOR_ADMIN is an account which can access the bucket metadata
REM OBJSTOR_ADMIN and OBJSTOR_PASS are optional
SET SA_KEY=%1
SET CLUSTER_URL=%2
SET OBJSTOR_ADMIN=%3
SET OBJSTOR_PASS=%4
oc login --token=%SA_KEY% --server=%CLUSTER_URL%

REM Stash the pod name into a variable via a temporary file
REM ALLOWS_REMOTE_CONNECTIONS is a string which must match an environment value name on the pod via the deployment config
REM Pod name cannot have . or / in the name.
SET ENV_VARIABLE_NAME=ALLOWS_REMOTE_CONNECTIONS
oc get pods -o json | jq .items > auto_gen_temp_file
REM Replace . and / with _
powershell -Command "(gc auto_gen_temp_file) -replace '[\./]', '_' | Out-File -encoding ASCII auto_gen_temp_file"
REM Filter with JQ
type auto_gen_temp_file | jq "[.[] | { name: .metadata.name, containers: .spec.containers}]" | jq -r ".[] | select(.name != null) | select(.containers[] != null)| select(.containers[].env != null)| select(.containers[].env[] | .name == \"%ENV_VARIABLE_NAME%\")" | jq .name > auto_gen_temp_file2
REM Erase quotation marks
powershell -Command "(gc auto_gen_temp_file2) -replace '[\""]', '' | Out-File -encoding ASCII auto_gen_temp_file3"
REM Get value and run the command
SET /p POD_NAME= <auto_gen_temp_file3
start "oc-port-forward" cmd /k "SET PATH=%cd%;%PATH% & oc port-forward %POD_NAME% 5432:5432"

REM Run Python script which pulls data from object storage and sends to the database
IF "%3"=="" ( 
    "python.exe" relay_bucket_data.py
) ELSE ( 
    "python.exe" relay_bucket_data.py -objstor_admin %3 -objstor_pass %4
)

REM Clean up! Note: The extra space in "oc  port-forward*" is intentional; taskkill doesn't work without it
taskkill /FI "WindowTitle eq oc  port-forward %POD_NAME%*" /T /F
del temp-podname-file.txt
del auto_gen_temp_file
del auto_gen_temp_file2
del auto_gen_temp_file3
