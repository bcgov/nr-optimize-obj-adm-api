# Optimization Team contacts: Heather Hay and Peter Platten.
#
# Main Script File(s): search_objdels_no_tf_nonames.py
# Supporting Script File(s): .env, constants.py
#
# Purpose:
#   Searches an S3-compatible bucket for *all object deletions* (delete markers),
#   with no date constraints and no prior knowledge of object names.
#   Results are written to a CSV with object key, deletion date, and
#   the most recent previous version (if any).
#
# Author: Heather Hay
# Copyright: (c) Optimization Team 2025
#
# Created: May 2026

import boto3
import os
import csv
from datetime import datetime, timezone
from dotenv import load_dotenv

# ----------------------------------------------------------------------
# Ensure output directory exists
# ----------------------------------------------------------------------
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ----------------------------------------------------------------------
# Timestamp for output file
# ----------------------------------------------------------------------
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# ----------------------------------------------------------------------
# Load environment variables
# ----------------------------------------------------------------------
load_dotenv()
ACCESS_KEY = os.getenv("ACCESS_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
S3_ENDPOINT = os.getenv("S3_ENDPOINT")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_BUCKET_PREFIX = os.getenv("S3_BUCKET_PREFIX", "").strip()

# ----------------------------------------------------------------------
# Validate environment variables
# ----------------------------------------------------------------------
if not all([ACCESS_KEY, SECRET_KEY, S3_ENDPOINT, S3_BUCKET_NAME]):
    raise ValueError("Missing required AWS environment variables. Check your .env file.")

# ----------------------------------------------------------------------
# Initialize S3 client
# ----------------------------------------------------------------------
s3 = boto3.client(
    "s3",
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    endpoint_url=S3_ENDPOINT
)

# ----------------------------------------------------------------------
# Prepare paginator arguments (optional prefix scoping)
# ----------------------------------------------------------------------
paginator = s3.get_paginator("list_object_versions")
paginate_kwargs = {"Bucket": S3_BUCKET_NAME}

if S3_BUCKET_PREFIX:
    if not S3_BUCKET_PREFIX.endswith("/"):
        S3_BUCKET_PREFIX = S3_BUCKET_PREFIX + "/"
    paginate_kwargs["Prefix"] = S3_BUCKET_PREFIX

# ----------------------------------------------------------------------
# Collect results (do not write file yet)
# ----------------------------------------------------------------------
rows = []
count = 0

for page in paginator.paginate(**paginate_kwargs):
    delete_markers = page.get("DeleteMarkers", [])
    versions = page.get("Versions", [])

    # Index versions by key and sort newest → oldest
    versions_by_key = {}
    for v in versions:
        versions_by_key.setdefault(v["Key"], []).append(v)

    for key_versions in versions_by_key.values():
        key_versions.sort(
            key=lambda v: v["LastModified"],
            reverse=True
        )

    for marker in delete_markers:
        key = marker["Key"]
        deleted_at = marker["LastModified"]

        prev_id = ""
        prev_date = ""

        # Find most recent version prior to deletion
        if key in versions_by_key:
            for v in versions_by_key[key]:
                if v["LastModified"] < deleted_at:
                    prev_id = v["VersionId"]
                    prev_date = v["LastModified"].isoformat()
                    break

        if prev_id:
            prev_id_for_csv = f'="{prev_id}"'
        else:
            prev_id_for_csv = ""

        rows.append([
            S3_BUCKET_NAME,
            key,
            deleted_at.astimezone(timezone.utc).isoformat(),
            prev_id_for_csv,
            prev_date
        ])
        count += 1

# ----------------------------------------------------------------------
# Write output only if deletions found
# ----------------------------------------------------------------------
scoped = f" (scoped to prefix: {S3_BUCKET_PREFIX})" if S3_BUCKET_PREFIX else ""

if count > 0:
    output_csv = os.path.join(
        OUTPUT_DIR,
        f"bucket-all-deletions_{timestamp}.csv"
    )

    with open(output_csv, "w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            "Bucket",
            "Key",
            "DeletedAt",
            "PreviousVersionId",
            "PreviousVersionLastModified"
        ])
        writer.writerows(rows)

    print(
        f"Found {count} deletions{scoped}. "
        f"Results saved to {output_csv}."
    )
else:
    print(f"No deletions found{scoped}. No output file created.")
