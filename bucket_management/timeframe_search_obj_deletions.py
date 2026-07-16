"""
search_objdels_with_prefix_and_versions.py

Description:
    Searches an S3 bucket for deleted objects within a specified timeframe,
    optionally scoped by S3_BUCKET_PREFIX. Enhances original script by retrieving:

    - Object Key
    - Version ID
    - Creation Date (earliest version)
    - Last Modified Date (version)
    - Deletion Date (delete marker timestamp)

Requirements:
    - boto3
    - python-dotenv
    - constants.py (for env configuration)

Author: Revised by Copilot
"""

import boto3
import csv
from datetime import datetime, timezone
from dotenv import load_dotenv
import os

# -------------------------------
# Load environment variables
# -------------------------------
load_dotenv()

ACCESS_KEY = os.getenv("ACCESS_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
S3_ENDPOINT = os.getenv("S3_ENDPOINT")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_BUCKET_PREFIX = os.getenv("S3_BUCKET_PREFIX")  # <-- New: prefix support

# Validate required variables
if not all([
    ACCESS_KEY,
    SECRET_KEY,
    S3_ENDPOINT,
    S3_BUCKET_NAME
]):
    raise ValueError("Missing required AWS environment variables.")

# -------------------------------
# Prompt user for date range
# -------------------------------
start_input = input("Enter start date (YYYY-MM-DD): ")
end_input = input("Enter end date (YYYY-MM-DD): ")

start_date = datetime.strptime(start_input, "%Y-%m-%d").replace(tzinfo=timezone.utc)
end_date = datetime.strptime(end_input, "%Y-%m-%d").replace(tzinfo=timezone.utc)

# -------------------------------
# Initialize S3 client
# -------------------------------
s3 = boto3.client(
    "s3",
    ACCESS_KEY=ACCESS_KEY,
    SECRET_KEY=SECRET_KEY,
    endpoint_url=S3_ENDPOINT
)

# -------------------------------
# Data structures
# -------------------------------

# Store ALL versions per key so we can derive creation + last modified
versions_lookup = {}

# Store matching deletions
deletions = []

# -------------------------------
# Paginate object versions
# -------------------------------
paginator = s3.get_paginator("list_object_versions")

pagination_args = {
    "Bucket": S3_BUCKET_NAME,
}

# Apply prefix filtering if provided
if S3_BUCKET_PREFIX:
    pagination_args["Prefix"] = S3_BUCKET_PREFIX

def clean_string(value):
    """
    Removes problematic non-printable or zero-width characters
    that commonly appear in object keys.
    """
    if not value:
        return value

    return (
        value
        .replace("\u200c", "")  # zero-width non-joiner
        .replace("\u200b", "")  # zero-width space
        .strip()
    )

for page in paginator.paginate(**pagination_args):

    # ---------------------------
    # Collect object versions
    # ---------------------------
    if "Versions" in page:
        for version in page["Versions"]:
            key = version["Key"]

            if key not in versions_lookup:
                versions_lookup[key] = []

            versions_lookup[key].append({
                "VersionId": version["VersionId"],
                "LastModified": version["LastModified"]
            })

    # ---------------------------
    # Process delete markers
    # ---------------------------

    if "DeleteMarkers" in page:
        for marker in page["DeleteMarkers"]:
            deletion_date = marker["LastModified"]

            # Filter by timeframe
            if not (start_date <= deletion_date <= end_date):
                continue

            key = marker["Key"]
            version_id = marker["VersionId"]

            # Default values if no versions found
            creation_date = None
            last_modified = None

            if key in versions_lookup and versions_lookup[key]:
                # Sort versions chronologically
                sorted_versions = sorted(
                    versions_lookup[key],
                    key=lambda x: x["LastModified"]
                )

                # Earliest version = creation
                creation_date = sorted_versions[0]["LastModified"]

                # Latest version BEFORE deletion ≈ last modified
                last_modified = sorted_versions[-1]["LastModified"]

            deletions.append([
                clean_string(key),
                f'="{clean_string(version_id)}"',
                creation_date.isoformat() if creation_date else "",
                last_modified.isoformat() if last_modified else "",
                deletion_date.isoformat()
            ])

# -------------------------------
# Output results
# -------------------------------
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
output_file = f"bucket-deletions-with-metadata_{timestamp}.csv"

with open(output_file, "w", newline="", encoding="utf-8") as csvfile: 
    writer = csv.writer(csvfile)

    writer.writerow([
        "Key",
        "VersionId",
        "CreationDate",
        "LastModified",
        "DeletionDate"
    ])

    writer.writerows(deletions)

print(f"Found {len(deletions)} deletions. Results saved to {output_file}")