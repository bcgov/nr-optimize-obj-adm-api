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
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_S3_ENDPOINT = os.getenv("AWS_S3_ENDPOINT")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")
AWS_S3_PREFIX = os.getenv("AWS_S3_PREFIX", "").strip()

# ----------------------------------------------------------------------
# Validate environment variables
# ----------------------------------------------------------------------
if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_S3_ENDPOINT, AWS_S3_BUCKET]):
    raise ValueError("Missing required AWS environment variables. Check your .env file.")

# ----------------------------------------------------------------------
# Initialize S3 client
# ----------------------------------------------------------------------
s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    endpoint_url=AWS_S3_ENDPOINT
)

# ----------------------------------------------------------------------
# Prepare paginator arguments (optional prefix scoping)
# ----------------------------------------------------------------------
paginator = s3.get_paginator("list_object_versions")
paginate_kwargs = {"Bucket": AWS_S3_BUCKET}

if AWS_S3_PREFIX:
    if not AWS_S3_PREFIX.endswith("/"):
        AWS_S3_PREFIX = AWS_S3_PREFIX + "/"
    paginate_kwargs["Prefix"] = AWS_S3_PREFIX

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
            AWS_S3_BUCKET,
            key,
            deleted_at.astimezone(timezone.utc).isoformat(),
            prev_id_for_csv,
            prev_date
        ])
        count += 1

# ----------------------------------------------------------------------
# Write output only if deletions found
# ----------------------------------------------------------------------
scoped = f" (scoped to prefix: {AWS_S3_PREFIX})" if AWS_S3_PREFIX else ""

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
