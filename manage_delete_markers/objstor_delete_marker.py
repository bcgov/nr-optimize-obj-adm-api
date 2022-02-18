# -------------------------------------------------------------------------------
# Name:        objstor_delete_marker.py
# Purpose:     Clean up excessive delete markers in S3 buckets
#
# Author:      HHAY, PPLATTEN
#
# Created:     2022-01-31
# -------------------------------------------------------------------------------

import sys
import constants
# import time

# from datetime import datetime

from minio import Minio
from minio.error import S3Error
# from ecsclient.common.exceptions import ECSClientException
# from ecsclient.client import Client as ESCCLlient
# from boto3 import client


# # login to the administrative DELL ECS API
# def adminLogin(user, password, endpoint):
#     client = ESCCLlient(
#         "3",
#         username=user,
#         password=password,
#         token_endpoint=endpoint + "/login",
#         cache_token=False,
#         ecs_endpoint=endpoint,
#     )

#     print("----------LOGGED IN ADMIN USER IS:")
#     print(client.user_info.whoami())
#     print()
#     return client


# def try_admin_login(user, password, endpoint):
#     client = None
#     try:
#         client = adminLogin(user, password, endpoint)
#     except ECSClientException:
#         counter = 3
#         while counter > 0:
#             print("Connection to S3 Failed, trying again in 10")
#             time.sleep(10)
#             try:
#                 client = adminLogin(constants.OBJSTOR_ADMIN, constants.OBJSTOR_ADMIN_PASS, constants.OBJSTOR_MGMT_ENDPOINT)
#                 counter = 0
#             except ECSClientException:
#                 if counter == 1:
#                     print("Connection to S3 Failed, closing")
#                 pass
#             counter = counter - 1
#     return client


# def get_bucket_infos(namespace, client):
#     print(
#         "Getting a list of buckets within the " + namespace + " namespace:"
#     )

#     # Get a list of bucket names. Don't stop at the default of 100 buckets (nrs is at 73 on 2021-05-27)
#     namespace_response = client.bucket.list(namespace, limit=10000)
#     bucket_list = namespace_response["object_bucket"]
#     bucket_dict = {}
#     for bucket in bucket_list:
#         bucket_dict[bucket['name']] = {
#             'name': bucket['name']
#         }
#     return bucket_dict


# def get_bucket_dms(client, bucket_name, dm_margin, total_object_count):

#     bucket_files = client.list_objects(
#         bucket_name,
#         recursive=True,
#         use_url_encoding_type=False,
#         include_version=True
#     )

#     trimmed_files = []
#     increment = total_object_count/100
#     logging_margin = 10000
#     if increment < logging_margin:
#         increment = logging_margin
#     trim_file_count = 0
#     for bucket_file in bucket_files:
#         trim_file_count += 1
#         if (not trim_file_count == 0 or trim_file_count > logging_margin) and trim_file_count % increment == 0:
#             percent_complete = (trim_file_count/total_object_count)*100
#             print(f"Trimmed {trim_file_count} files... {percent_complete}%")
#         # filter down to only delete markers
#         if bucket_file.is_dir:
#             continue
#         if not bucket_file.is_delete_marker:
#             continue
#         # create file stub to save ram
#         trimmed_files.append({
#             'object_name': bucket_file.object_name,
#             'version_id': bucket_file.version_id
#         })
#     bucket_files = trimmed_files
#     trimmed_files = None

#     files_in_bucket = len(bucket_files)
#     if files_in_bucket > 10000:
#         print(f"Note: Large bucket with {files_in_bucket} objects")

#     dms_by_file = {}
#     dm_counts = {}
#     obj_counter = 0
#     for bucket_file in bucket_files:
#         if not obj_counter == 0 and obj_counter % 10000 == 0:
#             percent = (obj_counter/files_in_bucket)*100
#             hr = datetime.now().hour
#             m = datetime.now().minute
#             s = datetime.now().second
#             print(f"{percent,2}: Checked in {obj_counter} objects for bucket {bucket_name}... {hr}:{m}:{s}")
#         obj_counter += 1

#         file_name = bucket_file['object_name']

#         # initialize dms_by_file dictionary
#         if file_name not in dms_by_file:
#             dms_by_file[file_name] = []
#         dms_by_file[file_name].append(bucket_file)
#     bucket_files = None

#     excessive_dms = False
#     for file_name in dms_by_file:
#         # if file_name == "version testing/test.txt":
#         versions = dms_by_file[file_name]
#         count = len(versions)
#         if count > dm_margin:
#             print(f'{count},{bucket_name},{file_name}')
#             excessive_dms = True
#         continue
#         versions.sort(
#             key=lambda s: s['version_id'],
#             reverse=True
#         )
#         marker_count = 0
#         for version in versions:
#             marker_count += 1
#             # if marker_count > dm_margin:
#             #     minio_client.remove_object(constants.OBJSTOR_BUCKET, file_name, version.version_id)
#         if marker_count > dm_margin:
#             dm_counts[file_name] = marker_count

#     return excessive_dms


def print_versions(client, bucket_name, file_name):
    response = client.list_objects(
        bucket_name,
        recursive=False,
        prefix=file_name,
        use_url_encoding_type=False,
        include_version=True
    )
    
    # response = client.stat_object(bucket_name, file_name)

    for file in response:
        if file.object_name == file_name:
            is_delete_marker = file.is_delete_marker
            print(f"Marker: {is_delete_marker}, Name: {file_name}")


def main(argv):

    bucket_names = constants.BUCKETS.split(",")

    # try:
    #     # connect to S3
    #     s3 = client(
    #         "s3",
    #         endpoint_url=constants.OBJSTOR_MGMT_ENDPOINT,
    #         aws_access_key_id=constants.OBJSTOR_ACCESS_KEY,
    #         aws_secret_access_key=constants.OBJSTOR_SECRET_KEY,
    #     )

    #     resp = s3.list_buckets()

    #     resp = s3.list_objects_v2(Bucket=constants.OBJSTOR_BUCKET)
    #     # create empty list to hold variable values
    #     listOfMainFolder = []
    #     listOfMainFolderSize = []
    #     listofFullPath = []
    #     listofFullPathSize = []
    #     listofMainCost = []
    #     listofSubCost = []

    #     for key in resp["Contents"]:
    #         # list key and size of folder
    #         mainfolder = key["Key"].split("/")[0]
    #         fullpath = key["Key"].rsplit("/", 1)[0]
    #         size_in_mb = key["Size"] / (1 << 20)
    #         size_in_gb = key["Size"] / (1 << 30)
    #         maincost = size_in_gb * 0.07
    #         subcost = key["Size"] / (1 << 30) * 0.07

    #         # read variable values into lists
    #         listOfMainFolder.append(mainfolder)
    #         listOfMainFolderSize.append(size_in_gb)
    #         listofFullPath.append(fullpath)
    #         listofFullPathSize.append(size_in_mb)
    #         listofMainCost.append(maincost)
    #         listofSubCost.append(subcost)
    # except Exception as error:
    #     print(error)

    minio_client = Minio(
        endpoint=constants.OBJSTOR_ENDPOINT,
        access_key=constants.OBJSTOR_ACCESS_KEY,
        secret_key=constants.OBJSTOR_SECRET_KEY,
        region="US",
    )

    file_list = [
        "WF-DISPATCH/bottom.bcgov/dispatch-middleware-war/trappist.log.1",
        "WF-WFWX/bottom.bcgov/wfwx-datawriter-war/0-wfwx-datawriter-war.log",
        "CSNR-EMSWR/vermicelli.bcgov/emswr/APP-EMSWR.log",
        "CSNR-FARM/vermicelli.bcgov/farm/APP-FARM.log",
        "CSNR-FTLS/vermicelli.bcgov/ftls/APP-FTLS.log",
        "CSNR-GBMS/vermicelli.bcgov/gbms/APP-GBMS.log",
        "CSNR-oats/vermicelli.bcgov/oatsp/APP-OATSP.log",
        "CSNR-WEBADE/vermicelli.bcgov/adam-env/app-adam-env.log",
        "CSNR-ACAT/vermicelli.bcgov.sync.last",
        "CSNR-AQHI/vermicelli.bcgov.sync.last",
        "CSNR-ATA/vermicelli.bcgov.sync.last",
        "CSNR-ATLAS/vermicelli.bcgov.sync.last",
        "CSNR-ats/vermicelli.bcgov.sync.last",
        "CSNR-BARTS/vermicelli.bcgov.sync.last",
        "csnr-bmis/vermicelli.bcgov.sync.last",
        "CSNR-BMIS_HTML/vermicelli.bcgov.sync.last",
        "CSNR-CCSD/vermicelli.bcgov.sync.last",
        "CSNR-CHORAPWD/vermicelli.bcgov.sync.last",
        "CSNR-CLIR/vermicelli.bcgov.sync.last",
        "CSNR-cors/vermicelli.bcgov.sync.last",
        "CSNR-crispws/vermicelli.bcgov.sync.last",
        "CSNR-cvis/vermicelli.bcgov.sync.last",
        "CSNR-eirs/vermicelli.bcgov.sync.last",
        "CSNR-ELDS/vermicelli.bcgov.sync.last",
        "CSNR-EMSEDT/vermicelli.bcgov.sync.last",
        "CSNR-EMSEDT/vermicelli.bcgov/ems_ftp_sync.log",
        "CSNR-EMSWR/vermicelli.bcgov.sync.last",
        "CSNR-ESWP/vermicelli.bcgov.sync.last",
        "CSNR-FARM/vermicelli.bcgov.sync.last",
        "CSNR-FDMA/vermicelli.bcgov.sync.last",
        "CSNR-fidq/vermicelli.bcgov.sync.last",
        "CSNR-FPCT/vermicelli.bcgov.sync.last",
        "CSNR-FSPGEN/vermicelli.bcgov.sync.last",
        "CSNR-FTLS/vermicelli.bcgov.sync.last",
        "CSNR-GATOR/vermicelli.bcgov.sync.last",
        "CSNR-GBMS/vermicelli.bcgov.sync.last",
        "CSNR-HRPWSV/vermicelli.bcgov.sync.last",
        "CSNR-MAPVUNIX/vermicelli.bcgov.sync.last",
        "CSNR-MASCOTW/vermicelli.bcgov.sync.last",
        "CSNR-ngps/vermicelli.bcgov.sync.last",
        "CSNR-oats/vermicelli.bcgov.sync.last",
        "CSNR-ORDS/vermicelli.bcgov.sync.last",
        "CSNR-PAR/vermicelli.bcgov.sync.last",
        "CSNR-PSCIS/vermicelli.bcgov.sync.last",
        "CSNR-rec/vermicelli.bcgov.sync.last",
        "CSNR-SEA/vermicelli.bcgov.sync.last",
        "CSNR-SEEDMAP/vermicelli.bcgov.sync.last",
        "CSNR-sis/vermicelli.bcgov.sync.last",
        "CSNR-TTLSWS/vermicelli.bcgov.sync.last",
        "CSNR-WEBADE/vermicelli.bcgov.sync.last",
        "CSNR-WIMSI/vermicelli.bcgov.sync.last",
        "WF-WFSS/zone.bcgov.sync.last",
        "WF-WFHR/bottom.bcgov/wfhr-payroll-api-wfdlv/wfhr-payroll-api.log",
        "WF-WFHR/bottom.bcgov/wfhr-wps-payroll-sync-api/wfhr-wps-payroll-sync-api.log",
        "WF-WFONE/bottom.bcgov/wfone-quartzdesk-war/quartzdesk-web-trace.log.1",
        "WF-WFRM/bottom.bcgov/wfrm-war-wfdlv/wfrm-war.log",
        "WF-DISPATCH/bottom.bcgov/dispatch-middleware-war/trappist.log",
        "WF-DISPATCH/bottom.bcgov/dispatch-wfim-incident-sync-api/dispatch-wfim-incident-sync-api.log",
        "WF-DISPATCH/bottom.bcgov/dispatch-wfim-rof-sync-api/dispatch-wfim-rof-sync-api.log",
        "WF-WEBADE/bottom.bcgov/webade-oauth2-api/localhost_access_log.2022-02-17.log",
        "WF-WEBADE/bottom.bcgov/webade-oauth2-api/webade-oauth2-api.log",
        "ISSS-INFRA/sevenup.bcgov.sync.last",
        "ISSS-NPE/sevenup.bcgov.sync.last",
        "WF-DISPATCH/bottom.bcgov.sync.last",
        "WF-RRT/bottom.bcgov.sync.last",
        "WF-WEBADE/bottom.bcgov.sync.last",
        "WF-WFCST/bottom.bcgov.sync.last",
        "WF-WFDM/bottom.bcgov.sync.last",
        "WF-WFDM/bottom.bcgov/wfdm-document-management-api/wfdm-document-management-api.log",
        "WF-WFFIN/bottom.bcgov.sync.last",
        "WF-WFHR/bottom.bcgov.sync.last",
        "WF-WFIM/bottom.bcgov.sync.last",
        "WF-WFIM/bottom.bcgov/wfim-dispatch-2020-incident-sync-api/wfim-dispatch-2020-incident-sync-api.log",
        "WF-WFIM/bottom.bcgov/wfim-dispatch-2020-rof-sync-api/wfim-dispatch-2020-rof-sync-api.log",
        "WF-WFIM/bottom.bcgov/wfim-incidents-api-wfdlv/wfim-incidents-api.log",
        "WF-WFONE/bottom.bcgov.sync.last",
        "WF-WFONE/bottom.bcgov/wfone-quartzdesk-war/quartzdesk-web-trace.log",
        "WF-WFONE/bottom.bcgov/wfone-quartzdesk-war/quartzdesk-web.log",
        "WF-WFONE/bottom.bcgov/wfone-vendor-portal-api/wfone-vendor-portal-api.log",
        "WF-WFONE/bottom.bcgov/wfone-workflow-admin-war-wfdlv/wfone-workflow-admin-war.log",
        "WF-WFONE/bottom.bcgov/wfone-workflow-api-wfdlv/wfone-workflow-api.log",
        "WF-WFORG/bottom.bcgov.sync.last",
        "WF-WFRM/bottom.bcgov.sync.last",
        "WF-WFRM/bottom.bcgov/wfrm-employee-sync-api/wfrm-employee-sync-api.log",
        "WF-WFRM/bottom.bcgov/wfrm-resources-api/wfrm-resources-api.log",
        "WF-WFRM/bottom.bcgov/wfrm-resources-v2-api/wfrm-resources-v2-api.log",
        "WF-WFSS/bottom.bcgov.sync.last",
        "WF-WFWM/bottom.bcgov.sync.last",
        "WF-WFWX/bottom.bcgov.sync.last",
        "WF-WFONE/transform.bcgov.sync.last",
        "ISSS-CFSWEB/anomoly.bcgov/cfsweb-war/cfsweb-war.log",
        "ISSS-CFSWEB/anomoly.bcgov/cfsweb-war/localhost_access_log.2022-02-17.log",
        "ISSS-FFS/anomoly.bcgov/ffs-server-war/localhost_access_log.2022-02-17.log",
        "CSNR-ats/alexandria.sync.last",
        "CSNR-cors/alexandria.sync.last",
        "CSNR-ffs/alexandria.sync.last",
        "CSNR-ilrr/alexandria.sync.last",
        "CSNR-rar/alexandria.sync.last",
        "ISSS-AS/anomoly.bcgov/as-as-api/as-as-api.log",
        "ISSS-AS/anomoly.bcgov/as-as-api/localhost_access_log.2022-02-17.log",
        "ISSS-liferay-int3/anomoly.bcgov/portlets/AS/as-client-portlet/nrs_as_client_ui.log",
        "ISSS-liferay-int3/anomoly.bcgov/portlets/NRSCMN/nrscmn-liferay-portlet/nrscmn_liferay_portlet_security_redirect_hook.log",
        "ISSS-FNCS/anomoly.bcgov/fncs-client-war/catalina.2022-02-17.log",
        "ISSS-FNCS/anomoly.bcgov/fncs-client-war/localhost_access_log.2022-02-17.log",
        "ISSS-AQUA/anomoly.bcgov.sync.last",
        "ISSS-ARTS/anomoly.bcgov.sync.last",
        "ISSS-AS/anomoly.bcgov.sync.last",
        "ISSS-ATS/anomoly.bcgov.sync.last",
        "ISSS-CCSC/anomoly.bcgov.sync.last",
        "ISSS-CFSC/anomoly.bcgov.sync.last",
        "ISSS-CFSWEB/anomoly.bcgov.sync.last",
        "ISSS-CIRRAS/anomoly.bcgov.sync.last",
        "ISSS-CWM/anomoly.bcgov.sync.last",
        "ISSS-CWMS/anomoly.bcgov.sync.last",
        "ISSS-DGEN/anomoly.bcgov.sync.last",
        "ISSS-DMS/anomoly.bcgov.sync.last",
        "ISSS-EDQA/anomoly.bcgov.sync.last",
        "ISSS-EYOR/anomoly.bcgov.sync.last",
        "ISSS-FFS/anomoly.bcgov.sync.last",
        "ISSS-FHD/anomoly.bcgov.sync.last",
        "ISSS-FNCS/anomoly.bcgov.sync.last",
        "ISSS-FNCS/anomoly.bcgov/fncs-client-war/fncs-client-war.log",
        "ISSS-FNCS/anomoly.bcgov/fncs-fncs-api/fncs-fncs-api.log",
        "ISSS-FNCS/anomoly.bcgov/fncs-fncs-api/localhost_access_log.2022-02-17.log",
        "ISSS-fnp/anomoly.bcgov.sync.last",
        "ISSS-FTA/anomoly.bcgov.sync.last",
        "ISSS-HRC/anomoly.bcgov.sync.last",
        "ISSS-ILRR/anomoly.bcgov.sync.last",
        "ISSS-INFRA/anomoly.bcgov.sync.last",
        "ISSS-ISMC/anomoly.bcgov.sync.last",
        "ISSS-liferay-int3/anomoly.bcgov.sync.last",
        "ISSS-MASCOTW/anomoly.bcgov.sync.last",
        "ISSS-MMS/anomoly.bcgov.sync.last",
        "ISSS-MWSL/anomoly.bcgov.sync.last",
        "ISSS-NPE/anomoly.bcgov.sync.last",
        "ISSS-NRISWS/anomoly.bcgov.sync.last",
        "ISSS-NRSSF/anomoly.bcgov.sync.last",
        "ISSS-RAAD3/anomoly.bcgov.sync.last",
        "ISSS-RAR/anomoly.bcgov.sync.last",
        "ISSS-RRS/anomoly.bcgov.sync.last",
        "ISSS-RRS/anomoly.bcgov/rrs-listener-war/rrs-listener-war.log",
        "ISSS-SNCSC/anomoly.bcgov.sync.last",
        "ISSS-SOS/anomoly.bcgov.sync.last",
        "ISSS-STES/anomoly.bcgov.sync.last",
        "ISSS-SUITT/anomoly.bcgov.sync.last",
        "ISSS-SWISBCG/anomoly.bcgov.sync.last",
        "ISSS-titan/anomoly.bcgov.sync.last",
        "ISSS-TTLS/anomoly.bcgov.sync.last",
        "ISSS-WEBADE/anomoly.bcgov.sync.last",
        "ISSS-WEBADE/anomoly.bcgov/webade-oauth2-api/localhost_access_log.2022-02-17.log",
        "ISSS-WEBADE/anomoly.bcgov/webade-oauth2-api/webade-oauth2-api.log",
        "ISSS-INFRA/glados.bcgov.sync.last",
        "ISSS-JCRS/glados.bcgov.sync.last",
        "ISSS-NPE/glados.bcgov.sync.last",
        "ISSS-nrsrs/glados.bcgov.sync.last",
        "ISSS-titan/glados.bcgov.sync.last",
        "CSNR-JCRS/android.bcgov.sync.last",
        "CSNR-JCRS/android.bcgov/localhost_access_log.2022-02-17.log",
        "HOME14/home14.log",
        "ISSS-JCRS/android.bcgov.sync.last"
    ]
  
    for file_name in file_list:
        print_versions(minio_client, "yieobs", file_name.lower())


    # ecs_client = try_admin_login(constants.OBJSTOR_ADMIN, constants.OBJSTOR_ADMIN_PASS, constants.OBJSTOR_MGMT_ENDPOINT)
    # if ecs_client is None:
    #     print("Unable to connect to S3")
    #     return

    # # only both collecting files with > dm margin delete markers
    # dm_margin = 2
    # dm_list = []
    # no_dm_list = []
    # exception_list = []
    # for bucket_name in bucket_names:
    #     print(f"Checking bucket: {bucket_name}.")
    #     try:
    #         object_count = ecs_client.bucket.getbucketdetails(constants.OBJSTOR_MGMT_NAMESPACE, bucket_name)['total_objects']
    #         print(f"Bucket has {object_count} objects. Trimming.")
    #         excessive_dms = get_bucket_dms(minio_client, bucket_name, dm_margin, object_count)
    #         if excessive_dms:
    #             dm_list.append(bucket_name)
    #         else:
    #             no_dm_list.append(bucket_name)
    #     except (Exception) as error:
    #         print(error)
    #         exception_list.append(bucket_name)

    # print("The following buckets had excessive Delete Markers: "+",".join(dm_list))
    # print("The following buckets had exceptions when checking: "+",".join(exception_list))
    # print("No above margin Delete Markers were found on the following buckets: "+",".join(no_dm_list))
    # print("Finished Report")


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except S3Error as exc:
        print("error occurred.", exc)
