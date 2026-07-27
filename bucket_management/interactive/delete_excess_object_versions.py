# -------------------------------------------------------------------------------
# Name:        delete_bucket_versions.py
# Purpose:     the purpose of the script is to scan an object storage bucket for 
#              high file version counts, and delete them.
#
# Author:      HHAY, PPLATTEN
#
# Created:     2026-07-24
# Copyright:   (c) OPTIMIZATION TEAM 2026
# Licence:     mine
#
#
# usage: 'delete_bucket_versions.py
# example: 'delete_bucket_versions.py'
# -------------------------------------------------------------------------------

# import python libraries
from boto3_helpers.auth import get_client
from boto3_helpers.searches import get_all_version_counts
from constants import BUCKET_NAME, TEMP_DIR
import os
from time import sleep
from utilities.file_helper import write_list_to_new_file
from utilities.log_helper import LOGGER


# create a client with S3, the access key, secret key, and public endpoint.
s3_client = get_client()

# set a maximum amount of versions for each file
maximum_versions = 10

# name the text file that is saved to your output folder
output_path = os.path.join(TEMP_DIR, f"{BUCKET_NAME}_filenames.txt")

# placeholder list for the list_file_names
list_file_names = []

use_existing_file = False
# Check if we want to use an existing file or create a new one
if os.path.exists(output_path):
    confirm = input(f"File {output_path} already exists. Do you want to re-use previous scan? (Y/N): ")
    if confirm.capitalize() == "Y":
        use_existing_file = True

if use_existing_file:
    # read the list of filenames and file counts from a text file
    with open(output_path, "r") as f: # change the folder path to suit your needs
        for line in f:
            key, count = line.strip().split(',')
            list_file_names.append(key)
else:
    list_file_names = get_all_version_counts(s3_client)
    # reduce the list of file names to only keys with over the maximum count
    list_file_names = {key: value for key, value in list_file_names.items() if value > maximum_versions}
    
    write_list_to_new_file(list_file_names)
    LOGGER.info(f"Found {len(list_file_names)} files with more than {maximum_versions} versions.")
    LOGGER.info(f"List of files and version counts written to {output_path}.")

# allow user to check the text file before confirming delete
confirm = input("Confirm Delete (Y/N):")
if confirm.capitalize()=="Y":

    # for each object with over maximum_versions
    for line in list_file_names:
        # get all versions of that object
        result = s3_client.list_object_versions(Bucket=BUCKET_NAME,Prefix=line)
        delete_objects=[]
        counter = 0
        for item in result["Versions"]:
            # if counter < maximum_versions:
            if counter < 5:
                counter+=1
                continue
            # after skipping the allowed versions, create dict of versions to delete
            delete_objects.append({"Key":line,"VersionId":item["VersionId"]})
        LOGGER.info(f"Deleting {len(delete_objects)} from {line}")
        # delete unwanted versions
        result = s3_client.delete_objects(Bucket=BUCKET_NAME,Delete={'Objects': delete_objects})
        LOGGER.info(f"Deleted {len(result['Deleted'])} from {line}")