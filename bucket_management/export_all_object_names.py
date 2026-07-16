# -------------------------------------------------------------------------------
# Name:        export_all_object_names.py
# Purpose:     the purpose of the script is to scan an object storage bucket for 
#              filenames and export a list of all files:
#              1.) you will need an .env file for key/value pairs and a constant.py file to successfully run this script
#              2.) connect to S3 Object Storage bucket
#              3.) read object keys to list
#              4.) iterate over list, write file names to a csv file
#
# Author:      PPLATTEN
#
# Created:     2026-06-29
# Copyright:   (c) OPTIMIZATION TEAM 2026
# Licence:     mine
#
# -------------------------------------------------------------------------------

import boto3
from botocore.config import Config as botocoreConfig
import constants


while True:
    # create a client with S3, the access key, secret key, and public endpoint.
    botoconfig = botocoreConfig(
        s3 = {"payload_signing_enabled": True}
    )
    boto_client = boto3.client(
        "s3",
        aws_access_key_id=constants.ACCESS_KEY,
        aws_secret_access_key=constants.SECRET_KEY,
        endpoint_url=constants.S3_ENDPOINT,
        config=botoconfig
    )

    bucket = constants.S3_BUCKET_NAME


    # get a list of bucket file names
    def get_undeleted_filenames(client: boto3.client):
        # placeholder list for the filenames
        filenames = []

        # list_objects_v2 ignores deleted files
        paginator = client.get_paginator('list_objects_v2')

        operation_parameters = {'Bucket': bucket, 'Prefix': 'file'}
        # operation_parameters = {'Bucket': bucket}
        page_iterator = paginator.paginate(**operation_parameters)

        # page_iterator = paginator.paginate(Bucket=bucket)
        for page in page_iterator:
            if "Contents" in page:
                for item in page["Contents"]:
                    filenames.append(item["Key"])
            else:
                print("No files found in bucket.")

        return filenames

    # get a list of bucket file names where the latest version have delete markers
    def get_deleted_filenames(client: boto3.client):
        # placeholder list for the filenames
        filenames = []

        # list_objects_v2 ignores deleted files
        paginator = client.get_paginator('list_object_versions')

        operation_parameters = {'Bucket': bucket}
        # operation_parameters = {'Bucket': bucket}
        page_iterator = paginator.paginate(**operation_parameters)

        # page_iterator = paginator.paginate(Bucket=bucket)
        for page in page_iterator:
            if "DeleteMarkers" in page:
                for item in page["DeleteMarkers"]:
                    if item["IsLatest"] == True:
                        filenames.append(item["Key"])

        return filenames

    # get a list of bucket all file names including soft deleted files
    def get_all_filenames(client: boto3.client):
        # placeholder list for the filenames
        filenames = []

        # list_objects_v2 ignores deleted files
        paginator = client.get_paginator('list_object_versions')

        operation_parameters = {'Bucket': bucket}
        # operation_parameters = {'Bucket': bucket}
        page_iterator = paginator.paginate(**operation_parameters)

        # page_iterator = paginator.paginate(Bucket=bucket)
        for page in page_iterator:
            if "Versions" in page:
                for item in page["Versions"]:
                    if item["IsLatest"] == True:
                        filenames.append(item["Key"])
            if "DeleteMarkers" in page:
                for item in page["DeleteMarkers"]:
                    if item["IsLatest"] == True:
                        filenames.append(item["Key"])

        return filenames

    # write the list of filenames to a text file
    def write_list(list=[], path="C:/Temp/bucket_filenames.txt"):
        with open(path, "w", encoding="utf-8") as f: # change the folder path to suit your needs
            for line in list:
                f.write(line)
                f.write("\n")

    # list_file_names = get_deleted_filenames(boto_client)
    # list_file_names = get_undeleted_filenames(boto_client)
    list_file_names = get_all_filenames(boto_client)

    # name the text file that is saved to your output folder
    path=f"C:/Git_Repo/Output/{bucket}_filenames.txt"

    write_list(list_file_names, path=path)

    print(f"List of files written to {path}.")