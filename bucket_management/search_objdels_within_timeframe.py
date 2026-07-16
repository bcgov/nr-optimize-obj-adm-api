# Optimization Team contacts: Heather Hay and Peter Platten.
#
# Main Script File(s): search_objdels_within_timeframe.py
# Supporting Script File(s): .env, constants.py
#
# Purpose: This Python script uses .env and constants.py to read in the user's object storage credentials and
# make a connection to their bucket. It then prompts the user for a start date and end date, and searches for # any object deleted within this timeframe. It outputs a csv file when complete with object key, date of 
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
ACCESS_KEY = os.getenv("ACCESS_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
S3_ENDPOINT = os.getenv("S3_ENDPOINT")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

# Validate environment variables
if not all([ACCESS_KEY, SECRET_KEY, S3_ENDPOINT, S3_BUCKET_NAME]):
    raise ValueError("Missing required AWS environment variables. Check your .env file.")

# Prompt user for date range
start_input = input("Enter start date (YYYY-MM-DD): ")
end_input = input("Enter end date (YYYY-MM-DD): ")
start_date = datetime.strptime(start_input, "%Y-%m-%d").replace(tzinfo=timezone.utc)
end_date = datetime.strptime(end_input, "%Y-%m-%d").replace(tzinfo=timezone.utc)

# Initialize S3 client
s3 = boto3.client(
    's3',
    ACCESS_KEY=ACCESS_KEY,
    SECRET_KEY=SECRET_KEY,
    endpoint_url=S3_ENDPOINT
)

deletions = []

# Paginate through object versions
paginator = s3.get_paginator('list_object_versions')
for page in paginator.paginate(Bucket=S3_BUCKET_NAME):
    if 'DeleteMarkers' in page:
        for marker in page['DeleteMarkers']:
            last_modified = marker['LastModified']
            if start_date <= last_modified <= end_date:
                deletions.append([
                    marker['Key'],
                    last_modified.isoformat(),
                    marker['VersionId']
                ])

# Write results to CSV
output_file = f"bucket-timeframe-deletions_{timestamp}.csv"
with open(output_file, "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Key", "DeletedAt", "VersionId"])
    writer.writerows(deletions)

print(f"Found {len(deletions)} deletions. Results saved to {output_file}.")
