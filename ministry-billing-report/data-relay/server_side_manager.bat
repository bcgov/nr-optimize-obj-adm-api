


REM Run using: server_side_manager.bat SA_KEY CLUSTER_URL
REM SA_KEY is the service account key from OpenShift.
REM CLUSTER_URL is https://api.silver.devops.gov.bc.ca:6443
SET SA_KEY=%1
SET CLUSTER_URL=%2
oc login --token=%SA_KEY% --server=%CLUSTER_URL%

REM Stash the pod name into a variable via a temporary file
REM ALLOWS_REMOTE_CONNECTIONS is a string which must match an environment value name on the pod via the deployment config
REM Pod name cannot have . or / in the name.
SET ENV_VARIABLE_NAME=ALLOWS_REMOTE_CONNECTIONS
oc get pods -o json | jq .items | tr ./ _ | jq "[.[] | { name: .metadata.name, containers: .spec.containers}]" | jq -r ".[] | select(.name != null) | select(.containers[] != null)| select(.containers[].env != null)| select(.containers[].env[] | .name == \"%ENV_VARIABLE_NAME%\")" | jq .name | sed 's/"//g;w temp-podname-file.txt'
SET /p POD_NAME= <temp-podname-file.txt
start "oc-port-forward" cmd /k "SET PATH=%cd%;%PATH% & oc port-forward %POD_NAME% 5432:5432"

REM TODO: Add Run command for the Python script which interacts with the database!!!!

REM Clean up!
taskkill /FI "WindowTitle eq oc-port-forward" /T /F
rm temp-podname-file.txt
