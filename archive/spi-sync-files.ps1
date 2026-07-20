# This script is intended to synchronize data between an OpenShift Persistent Volume Claim and a
# bucket mounted as a network drive in Windows. It was originally created by Clecio for WIOF.
# Full usage instructions are located in IITD Optimize Confluence as of 2021-09-01

$OC_BIN='oc.exe'

$ENVIRONMENTS = @{
    DLV =  @{NAMESPACE= "b24326-dev"; SRC = "\\testappfiles.nrs.bcgov\wiof_dlvr\"; PVC = "wiof-dlvr-app-data-vol2"};
    TEST = @{NAMESPACE= "b24326-test"; SRC = "\\testappfiles.nrs.bcgov\wiof_test\"; PVC = "wiof-test-app-data-vol2"};
    PROD = @{NAMESPACE= "b24326-prod"; SRC = "\\appfiles.nrs.bcgov\wiof_prod\";     PVC = "wiof-prod-app-data-vol2"}
}

$env = 'TEST'
$NAMESPACE=$ENVIRONMENTS[$env]['NAMESPACE']
$SRC_UNC=$ENVIRONMENTS[$env]['SRC']
$PVC=$ENVIRONMENTS[$env]['PVC']

$ErrorActionPreference = "Continue"
& $OC_BIN whoami
if ($LASTEXITCODE -ne 0) { throw "Are you authenticated to OpenShift? 'oc whoami' returned $LASTEXITCODE" }

# from here on, stop/abort on Any error
$ErrorActionPreference = "Stop"

& $OC_BIN version --client
# if ($LASTEXITCODE -ne 0) { throw "Exit code is $LASTEXITCODE" }
# $PVC=$(& $OC_BIN -n "${NAMESPACE}" get pvc -l app=wiof-test --ignore-not-found -o custom-columns=POD:.metadata.name --no-headers | Select -First 1)

Write-Host "NAMESPACE:$NAMESPACE"
Write-Host "SRC:$SRC_UNC"
Write-Host "TARGET(PVC):$PVC"

$POD_RSYNC_OVERRIDES=@"
{
        "spec": {
            "containers": [
                {
                  "command": [
                        "/bin/bash",
                        "-c",
                        "sleep 5000"
                    ],
                    "image": "registry.access.redhat.com/rhel7/rhel-tools",
                    "name": "rsync-container",
                    "volumeMounts": [{
                        "mountPath": "/apps_data/wiof",
                        "name": "app-data"
                    }]
                }
            ],       
            "volumes": [
                {
                    "name": "app-data",
                    "persistentVolumeClaim": {
                        "claimName": "${PVC}"
                    }
                }
            ]
        }
}
"@ -replace "`n|`r" -replace '\s\s+', " " -replace '"', '"""'

try {
    Write-Host "Clearing any existing rsync pod"
    & $OC_BIN -n "${NAMESPACE}" delete pod/rsync-container --now --wait --ignore-not-found=true
    Write-Host "Creating rsync pod"
    & $OC_BIN -n "${NAMESPACE}" run rsync-container "--overrides=${POD_RSYNC_OVERRIDES}" --image=notused --restart=Never
    Write-Host "Waiting for rsync pod"
    & $OC_BIN -n "${NAMESPACE}" wait --timeout=300s --for=condition=Ready pod/rsync-container
    Write-Host "Rsyncing files from ${SRC_UNC} to /apps_data/wiof/"
    & $OC_BIN "--namespace=${NAMESPACE}" rsync --progress=true --no-perms=true '--exclude=.Trash*' '--exclude=.DAV*' '--exclude=.DS_Store' '--exclude=Thumbs.db' "${SRC_UNC}" "rsync-container:/apps_data/wiof/"
    Write-Host "Fixing permission/chmod"
    $ErrorActionPreference = "Continue"
    & $OC_BIN -n "${NAMESPACE}" rsh rsync-container chmod -R 0640 '/apps_data/wiof/'
    $ErrorActionPreference = "Stop"
    Write-Host "Rsyncing files from /apps_data/wiof/ to ${SRC_UNC}"
    & $OC_BIN "--namespace=${NAMESPACE}" rsync --progress=true --no-perms=true '--exclude=.Trash*' '--exclude=.DAV*' '--exclude=.DS_Store' '--exclude=Thumbs.db' "rsync-container:/apps_data/wiof/" "${SRC_UNC}"
}Finally {
    Write-Host "Terminating rsync pod"
    & $OC_BIN -n "${NAMESPACE}" delete pod/rsync-container --now --wait --ignore-not-found=true
}