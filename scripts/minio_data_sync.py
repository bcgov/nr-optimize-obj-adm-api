# -------------------------------------------------------------------------------
# Name:        minio_data_sync.py
# Purpose:     sync files between S3 buckets and OpenShift pvcs or windows directories
#
# Author:      HHAY, JMONTEBE, PPLATTEN
#
# Created:     2021-07-21
# Notes: This is a little-tested proof of concept upload/download functionality
# -------------------------------------------------------------------------------

import sys
import constants
import os

from datetime import datetime
from minio import Minio
from minio.error import S3Error

pvc_directory = "C:\\TEMP\\sync-files-dir\\testfolder"


# copy a pvc file to bucket
def copy_to_bucket(minio_client, file_name):
    print("copying to bucket: ", file_name)
    return
    # upload file, never been run
    minio_client.fput_object(
        constants.OBJSTOR_BUCKET,
        file_name,
        os.path.join(pvc_directory, file_name),
    )


# copy a bucket file to pvc
def copy_to_pvc(minio_client, file_name, last_modified):
    print("copying to pvc: ", file_name)
    minio_client.fget_object(
        constants.OBJSTOR_BUCKET,
        file_name,
        os.path.join(pvc_directory, file_name),
    )
    os.utime(os.path.join(pvc_directory, file_name), (last_modified, last_modified))


def main(argv):

    minio_client = Minio(
        endpoint=constants.OBJSTOR_ENDPOINT,
        access_key=constants.OBJSTOR_ACCESS_KEY,
        secret_key=constants.OBJSTOR_SECRET_KEY,
        region="US",
    )

    # create a comparison dictionary
    file_dict = {}

    # add bucket file names and last modified timestamp to comparison dictionary
    bucket_files = minio_client.list_objects(
        constants.OBJSTOR_BUCKET, recursive=False, use_url_encoding_type=False
    )
    for bucket_file in bucket_files:
        file_name = bucket_file.object_name
        file_date = datetime.timestamp(bucket_file.last_modified)
        file_dict[file_name] = {
            "file_name": file_name,
            "bucket_last_modified": file_date
        }

    # add pvc file names and last modified timestamp to comparison dictionary
    file_names = os.listdir(pvc_directory)
    for name in file_names:
        file_name = name
        file_date = os.path.getmtime(os.path.join(pvc_directory, name))
        if file_name in file_dict:
            file_dict[file_name]["pvc_last_modified"] = file_date
        else:
            file_dict[file_name] = {
                "file_name": file_name,
                "pvc_last_modified": file_date
            }

    pvc_timestamp_sync_list = []
    # put newer bucket files into pvc, and newer pvc files into bucket, adjust timestamps
    for file_name in file_dict:
        file = file_dict[file_name]
        if "pvc_last_modified" in file and "bucket_last_modified" in file:
            # both directories have a copy of the file
            if file["pvc_last_modified"] > file["bucket_last_modified"]:
                # pvc has newer file
                copy_to_bucket(minio_client, file_name)
                pvc_timestamp_sync_list.append(file_name)
            elif file["pvc_last_modified"] < file["bucket_last_modified"]:
                # bucket has newer file
                copy_to_pvc(minio_client, file_name, file["bucket_last_modified"])
            # no work to do if the same last modified date
        elif "pvc_last_modified" in file:
            # file is only in the pvc
            copy_to_bucket(minio_client, file_name)
            pvc_timestamp_sync_list.append(file_name)
        else:
            # file is only in the bucket
            copy_to_pvc(minio_client, file_name, file["bucket_last_modified"])

    # sync the pvc timestamps up with the new bucket files, as we can't update timestamps on bucket files
    bucket_files = minio_client.list_objects(
        constants.OBJSTOR_BUCKET, recursive=False, use_url_encoding_type=False
    )
    for bucket_file in bucket_files:
        file_name = bucket_file.object_name
        bucket_last_modified = datetime.timestamp(bucket_file.last_modified)
        if file_name in pvc_timestamp_sync_list:
            os.utime(os.path.join(pvc_directory, file_name), (bucket_last_modified, bucket_last_modified))


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except S3Error as exc:
        print("error occurred.", exc)
