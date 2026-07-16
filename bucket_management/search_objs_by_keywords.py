# search_objs_by_keywords.py
#
# Purpose
#   - Read keywords from file_names.txt
#   - For any S3 key containing one of those keywords, report:
#       * if ANY delete marker exists in its history
#       * the MOST RECENT version's VersionId (and whether that latest is a delete marker)
#   - One row per object key (not per version)
#
# Author: Heather Hay
# Updated: 2026-05-12

import boto3
import os
import csv
from datetime import datetime
from dotenv import load_dotenv

# ----------------------------
# 1) Setup
# ----------------------------
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
load_dotenv()

OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

AWS_ACCESS_KEY_ID     = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_S3_ENDPOINT       = os.getenv("AWS_S3_ENDPOINT")
AWS_S3_BUCKET         = os.getenv("AWS_S3_BUCKET")
AWS_S3_PREFIX         = (os.getenv("AWS_S3_PREFIX") or "").strip()

if "&amp;" in AWS_S3_PREFIX:
    raise ValueError(
        "AWS_S3_PREFIX contains '&amp;'. "
        "S3 keys use literal '&'. Fix the .env value."
    )

if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_S3_ENDPOINT, AWS_S3_BUCKET]):
    raise ValueError("Missing required AWS environment variables. Check your .env file.")

# NOTE: utf-8-sig strips BOM characters that break substring matching
with open("file_names.txt", "r", encoding="utf-8-sig") as f:
    keywords_raw = [line.strip() for line in f if line.strip()]
KEYWORDS = [k.lower() for k in keywords_raw]

if not KEYWORDS:
    raise ValueError("No keywords loaded from file_names.txt.")

print(f"Loaded keywords: {KEYWORDS}")

def matches_key(key: str):
    """
    Return (True, matched_keyword) if the keyword appears anywhere
    in the full S3 key (path OR filename).

    This is a recursive, full-path substring search within the prefix.
    """
    lk = key.lower()

    for kw in KEYWORDS:
        if kw in lk:
            return True, kw

    return False, None

# ----------------------------
# 2) S3 pagination
# ----------------------------
s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    endpoint_url=AWS_S3_ENDPOINT,
)

agg = {}

paginator = s3.get_paginator("list_object_versions")
paginate_kwargs = {"Bucket": AWS_S3_BUCKET}

if AWS_S3_PREFIX:
    if not AWS_S3_PREFIX.endswith("/"):
        AWS_S3_PREFIX = AWS_S3_PREFIX + "/"
    paginate_kwargs["Prefix"] = AWS_S3_PREFIX
    print(f"Running with prefix scope: {AWS_S3_PREFIX}")
else:
    print("Running with full-bucket scope (no prefix filter)")

for page in paginator.paginate(**paginate_kwargs):

    # Normal versions
    for v in page.get("Versions", []):
        key = v["Key"]
        ok, matched_kw = matches_key(key)
        if not ok:
            continue

        last_mod = v["LastModified"]
        version_id = v.get("VersionId")

        rec = agg.get(key.lower())
        if (rec is None) or (last_mod > rec["latest_last_modified"]):
            agg[key.lower()] = {
                "Key": key,
                "matched_keyword": rec["matched_keyword"] if rec else matched_kw,
                "latest_last_modified": last_mod,
                "latest_version_id": version_id,
                "latest_is_delete_marker": False,
                "has_any_delete_marker": (rec["has_any_delete_marker"] if rec else False)
            }
        else:
            if rec and not rec.get("matched_keyword"):
                rec["matched_keyword"] = matched_kw

    # Delete markers
    for d in page.get("DeleteMarkers", []):
        key = d["Key"]
        ok, matched_kw = matches_key(key)
        if not ok:
            continue

        last_mod = d["LastModified"]
        version_id = d.get("VersionId")

        rec = agg.get(key.lower())
        if rec is None:
            agg[key.lower()] = {
                "Key": key,
                "matched_keyword": matched_kw,
                "latest_last_modified": last_mod,
                "latest_version_id": version_id,
                "latest_is_delete_marker": True,
                "has_any_delete_marker": True
            }
        else:
            rec["has_any_delete_marker"] = True
            if last_mod > rec["latest_last_modified"]:
                rec["latest_last_modified"] = last_mod
                rec["latest_version_id"] = version_id
                rec["latest_is_delete_marker"] = True
            if not rec.get("matched_keyword"):
                rec["matched_keyword"] = matched_kw

# ----------------------------
# 3) Write CSV only if results exist
# ----------------------------
records = sorted(
    agg.values(),
    key=lambda r: (r["Key"].lower(), r["latest_last_modified"])
)

scoped = f" (scoped to prefix: {AWS_S3_PREFIX})" if AWS_S3_PREFIX else ""

if len(records) == 0:
    print(f"No objects matched{scoped}. No output file created.")
else:
    output_file = os.path.join(
        OUTPUT_DIR,
        f"bucket_matched_objnames_{timestamp}.csv"
    )

    with open(output_file, "w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            "Key",
            "MatchedKeyword",
            "LatestLastModified",
            "LatestVersionId",
            "LatestIsDeleteMarker",
            "HasAnyDeleteMarker"
        ])
        for r in records:
            writer.writerow([
                r["Key"],
                r.get("matched_keyword"),
                r["latest_last_modified"].isoformat(),
                r["latest_version_id"],
                r["latest_is_delete_marker"],
                r["has_any_delete_marker"]
            ])

    print(f"{len(records)} object(s) matched{scoped}. Results saved to {output_file}.")