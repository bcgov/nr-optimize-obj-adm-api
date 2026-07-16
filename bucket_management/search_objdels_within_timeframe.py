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

# Initialize S3 client
s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    endpoint_url=AWS_S3_ENDPOINT
)

deletions = []

# Paginate through object versions
paginator = s3.get_paginator('list_object_versions')
for page in paginator.paginate(Bucket=AWS_S3_BUCKET):
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
