# Optimization Team contacts: Heather Hay and Peter Platten.
#
# Main Script File(s): restore_deleted_objects_namesknown.py
# Supporting Script File(s): .env, constants.py, file_names.txt
#
# Purpose: This Python script uses .env and constants.py to read in the user's object storage credentials and
# make a connection to their bucket. It then reads the list of object names provided in file_names.txt and 
# searches for any deleted objects with those names. It presents the found names and asks if the user wants to 
# continue with restoring these files to their most recent version. If the user types in yes, the script 
# proceeds to restore the files and outputs a log file when complete.
#
# Author: Heather Hay
# Copyright: (c) Optimization Team 2025
#
# Created: Nov 2025
# Updated:

import boto3
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_S3_ENDPOINT = os.getenv("AWS_S3_ENDPOINT")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")

# Validate environment variables
if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_S3_ENDPOINT, AWS_S3_BUCKET]):
    raise ValueError("Missing required AWS environment variables. Check your .env file.")

# Load object names from file_names.txt
with open("file_names.txt", "r") as f:
    object_names = [line.strip() for line in f if line.strip()]

# Initialize S3 client
s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    endpoint_url=AWS_S3_ENDPOINT
)

restored_objects = []
failed_objects = []
preview_objects = []

# Paginate through object versions for dry-run preview
paginator = s3.get_paginator('list_object_versions')
for page in paginator.paginate(Bucket=AWS_S3_BUCKET):
    delete_markers = page.get('DeleteMarkers', [])
    versions = page.get('Versions', [])

    for marker in delete_markers:
        key = marker['Key']
        if any(name in key for name in object_names):
            previous_versions = [v for v in versions if v['Key'] == key and v['LastModified'] < marker['LastModified']]
            previous_versions.sort(key=lambda v: v['LastModified'], reverse=True)
            if previous_versions:
                preview_objects.append(f"Would restore: {key} | versionId={marker['VersionId']}")

# Show dry-run preview
print("\nDry-run preview of objects to restore:")
for obj in preview_objects:
    print(obj)

# Ask for confirmation
confirm = input("\nDo you want to proceed with restoration? (yes/no): ").strip().lower()
if confirm == "yes":
    for page in paginator.paginate(Bucket=AWS_S3_BUCKET):
        delete_markers = page.get('DeleteMarkers', [])
        versions = page.get('Versions', [])

        for marker in delete_markers:
            key = marker['Key']
            if any(name in key for name in object_names):
                previous_versions = [v for v in versions if v['Key'] == key and v['LastModified'] < marker['LastModified']]
                previous_versions.sort(key=lambda v: v['LastModified'], reverse=True)
                if previous_versions:
                    version_id = marker['VersionId']
                    try:
                        s3.delete_object(Bucket=AWS_S3_BUCKET, Key=key, VersionId=version_id)
                        restored_objects.append(f"Restored: {key} | versionId={version_id}")
                    except Exception as e:
                        failed_objects.append(f"Failed: {key} | error={str(e)}")

    # Write log file
    log_file = f"restore-log_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
    with open(log_file, "w") as log:
        log.write("Restoration Summary\n")
        log.write("="*50 + "\n")
        log.write(f"Total restored: {len(restored_objects)}\n")
        log.write(f"Total failed: {len(failed_objects)}\n\n")

        log.write("Restored Objects:\n")
        log.write("\n".join(restored_objects) + "\n\n")

        if failed_objects:
            log.write("Failed Objects:\n")
            log.write("\n".join(failed_objects) + "\n")

    print(f"\nRestoration complete. Restored {len(restored_objects)} objects. Log saved to {log_file}.")
else:
    print("\nRestoration canceled.")