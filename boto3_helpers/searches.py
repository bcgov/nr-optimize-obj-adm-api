from boto3 import client, resource
from botocore.exceptions import ClientError
from boto3_helpers.auth import get_client, get_resource
from constants import BUCKET_NAME, TEMP_DIR
from utilities.log_helper import LOGGER
from utilities.file_helper import add_list_to_file
import re
import os

# Returns a count of uppercase files found
# Optionally Appends a list of uppercase file names to a file
def get_filenames_complex(s3_resource: resource, file_path: str = "", bucket_name: str = BUCKET_NAME, uppercase_only: bool = False, prefix: str = None, max: int = 0) -> bool:
    
    s3_client = s3_resource.meta.client
    paginator = s3_client.get_paginator('list_objects_v2')
    operation_parameters = {'Bucket': bucket_name}
    if prefix:
        operation_parameters['Prefix'] = prefix

    # This pattern matches any uppercase letters
    pattern = re.compile("[A-Z]")

    file_count = 0
    for page in paginator.paginate(**operation_parameters):
        found_files = []
        for obj in page.get('Contents', []):
            obj_key = obj['Key']
            if uppercase_only and not pattern.search(obj_key):
                continue
            else:
                found_files.append(obj_key)
            if max and len(found_files) >= max:
                break
        if file_path and found_files:
            add_list_to_file(file_path, found_files)
        file_count += len(found_files)

    return file_count

def save_all_filenames(s3_resource: resource, file_path: str, bucket_name: str = BUCKET_NAME, prefix: str = None) -> bool:
    file_count = get_filenames_complex(s3_resource, file_path=file_path, bucket_name=bucket_name, uppercase_only=False, prefix=prefix)
    return file_count

def get_all_filenames(s3_resource: resource, bucket_name: str = BUCKET_NAME, prefix: str = None) -> bool:
    path = os.path.join(TEMP_DIR, f"{BUCKET_NAME}_all_filenames.txt")
    file_count = get_filenames_complex(s3_resource, file_path=path, bucket_name=bucket_name, prefix=prefix)
    file_names = []
    if file_count > 0:
        with open(path, 'r') as f:
            file_names = f.read().splitlines()
    return file_names

def save_uppercase_filenames(s3_resource: resource, file_path: str, bucket_name: str = BUCKET_NAME, prefix: str = None) -> bool:
    file_count = get_filenames_complex(s3_resource, file_path=file_path, bucket_name=bucket_name, uppercase_only=True, prefix=prefix)
    return file_count

def get_versions_for_single_file():
    return

def get_all_version_counts(s3_client, bucket:str = BUCKET_NAME, prefix:str = ""):
    operation_parameters = {'Bucket': bucket}
    if prefix:
        operation_parameters['Prefix'] = prefix

    # get first 1000 objects
    result = s3_client.list_object_versions(**operation_parameters)
    # put all objects into a dictionary, with the value as a counter
    keyCount = {}

    # Return empty if no versions
    if "Versions" not in result:
        return keyCount
    
    for item in result["Versions"]:
        if item["Key"] not in keyCount:
            keyCount[item["Key"]] = 1
        else:
            keyCount[item["Key"]] += 1

    # if there are more than 1000 results, repeat the process until there are no extras
    continuationToken = result["NextKeyMarker"] if "NextKeyMarker" in result else None
    while continuationToken:   
        LOGGER.debug(continuationToken)   
        operation_parameters['KeyMarker'] = continuationToken
        result = s3_client.list_object_versions(**operation_parameters)
        if "Versions" in result:
            for item in result["Versions"]:
                if item["Key"] not in keyCount:
                    keyCount[item["Key"]] = 1
                else:
                    keyCount[item["Key"]] += 1
        else:
            if item["Key"] not in keyCount:
                keyCount[item["Key"]] = 1
            else:
                keyCount[item["Key"]] += 1
        continuationToken = result["NextKeyMarker"] if "NextKeyMarker" in result else None
    return keyCount