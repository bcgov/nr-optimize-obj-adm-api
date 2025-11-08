# Optimization Team contacts: Heather Hay and Peter Platten.
#
# Main Script File(s): search_objdels_within_tf_namesknown.py
# Supporting Script File(s): .env, constants.py, file_names.txt
#
# Purpose: This Python script uses .env and constants.py to read in the user's object storage credentials and
# make a connection to their bucket. It then reads the list of object names provided in file_names.txt, 
# prompts the user for a start date and end date, and searches for any object matching the filesnames that 
# were deleted within this timeframe. It outputs a csv file when complete with object key, date of 
# deletion, and version ID.
#
# Author: Heather Hay
# Copyright: (c) Optimization Team 2025
#
# Created: Nov 2025
# Updated:

import boto3
import os
import csv
from datetime import datetime, timezone
from dotenv import load_dotenv

# Generate timestamp for output file
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# Load environment variables
load_dotenv()
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_S3_ENDPOINT = os.getenv("AWS_S3_ENDPOINT")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")

# Validate environment variables
if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_S3_ENDPOINT, AWS_S3_BUCKET]):
    raise ValueError("Missing required AWS environment variables. Check your .env file.")

# Prompt user for date range
start_input = input("Enter start date (YYYY-MM-DD): ")
end_input = input("Enter end date (YYYY-MM-DD): ")
start_date = datetime.strptime(start_input, "%Y-%m-%d").replace(tzinfo=timezone.utc)
end_date = datetime.strptime(end_input, "%Y-%m-%d").replace(tzinfo=timezone.utc)

# Load keywords from file_names.txt
with open("file_names.txt", "r") as f:
    keywords = [line.strip().lower() for line in f if line.strip()]

# Initialize S3 client
s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    endpoint_url=AWS_S3_ENDPOINT
)

results = []

# Paginate through object versions
paginator = s3.get_paginator('list_object_versions')
for page in paginator.paginate(Bucket=AWS_S3_BUCKET):
    delete_markers = page.get('DeleteMarkers', [])
    versions = page.get('Versions', [])

    for marker in delete_markers:
        last_modified = marker['LastModified']
        key = marker['Key']
        if start_date <= last_modified <= end_date and any(k in key.lower() for k in keywords):
            # Find most recent version prior to deletion
            previous_versions = [v for v in versions if v['Key'] == key and v['LastModified'] < last_modified]
            previous_versions.sort(key=lambda v: v['LastModified'], reverse=True)
            prev_version_id = previous_versions[0]['VersionId'] if previous_versions else "None"
            prev_version_date = previous_versions[0]['LastModified'].isoformat() if previous_versions else "None"

            results.append([
                key,
                last_modified.isoformat(),
                prev_version_id,
                prev_version_date
            ])

# Write results to CSV
output_file = f"bucket-timeframe-deletions-namesearch_{timestamp}.csv"
with open(output_file, "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Key", "DeletedAt", "PreviousVersionId", "PreviousVersionLastModified"])
    writer.writerows(results)

print(f"Found {len(results)} matching deletions. Results saved to {output_file}.")