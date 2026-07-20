# Optimization Team contacts: Heather Hay and Peter Platten.
#
# Main Script File(s): search_objdels_within_timeframe.py
# Supporting Script File(s): .env, constants.py, file_names.txt
#
# Purpose: This Python script uses .env and constants.py to read in the user's object storage credentials and
# make a connection to their bucket. It then reads the list of object names provided in file_names.txt, 
# and searches for any object matching the file names including deleted objects. It outputs a csv file when 
# complete with object key, last modified date, version ID, and deletion marker (if any).
#
# Author: Heather Hay
# Copyright: (c) Optimization Team 2025
#
# Created: Nov 2025
# Updated:

import boto3
import os
import csv
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

ACCESS_KEY = os.getenv("ACCESS_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
S3_ENDPOINT = os.getenv("S3_ENDPOINT")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

# Validate environment variables
if not all([ACCESS_KEY, SECRET_KEY, S3_ENDPOINT, S3_BUCKET_NAME]):
    raise ValueError("Missing required AWS environment variables. Check your .env file.")

# Load keywords from file_names.txt
with open("file_names.txt", "r") as f:
    keywords = [line.strip().lower() for line in f if line.strip()]

# Initialize S3 client
s3 = boto3.client(
    's3',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    endpoint_url=S3_ENDPOINT
)

matches = {}

# Paginate through object versions
paginator = s3.get_paginator('list_object_versions')
for page in paginator.paginate(Bucket=S3_BUCKET_NAME):
    # Combine Versions and DeleteMarkers for full history
    all_versions = []
    if 'Versions' in page:
        all_versions.extend(page['Versions'])
    if 'DeleteMarkers' in page:
        all_versions.extend(page['DeleteMarkers'])

    for obj in all_versions:
        key = obj['Key'].lower()
        if any(keyword in key for keyword in keywords):
            # Track most recent version for each key
            if key not in matches or obj['LastModified'] > matches[key]['LastModified']:
                matches[key] = {
                    'Key': obj['Key'],
                    'LastModified': obj['LastModified'],
                    'VersionId': obj['VersionId'],
                    'IsDeleteMarker': 'DeleteMarker' in obj and obj['DeleteMarker']
                }

# Write results to CSV
with open("bucket_matched_objnames.csv", "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Key", "LastModified", "VersionId", "IsDeleteMarker"])
    for data in matches.values():
        writer.writerow([
            data['Key'],
            data['LastModified'].isoformat(),
            data['VersionId'],
            data['IsDeleteMarker']
        ])

print(f"Found {len(matches)} matching objects. Results saved to matched_objects.csv.")