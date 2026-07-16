"""
list_folder_tree_at_point_in_time.py

Description:
    Reconstructs S3 "_$folder$" objects as they existed at a specific
    timestamp and outputs a hierarchical folder tree.

Outputs:
    1. Tree view (console)
    2. Tree saved to .txt
    3. Optional CSV (flat list)

Author: Copilot (enhanced)
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
S3_BUCKET_PREFIX = os.getenv("S3_BUCKET_PREFIX")

if not all([
    ACCESS_KEY,
    SECRET_KEY,
    S3_ENDPOINT,
    S3_BUCKET_NAME
]):
    raise ValueError("Missing required AWS environment variables.")

# -------------------------------
# Prompt for timestamp
# -------------------------------
target_input = input("Enter target datetime (YYYY-MM-DD HH:MM:SS, UTC): ")
target_dt = datetime.strptime(target_input, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)

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
object_history = {}

# -------------------------------
# Helpers
# -------------------------------
def clean_string(value):
    if not value:
        return value

    return (
        value
        .replace("\u200c", "")
        .replace("\u200b", "")
        .strip()
    )

def insert_into_tree(tree, parts):
    """
    Inserts a list of folder parts into nested dict structure.

    Example:
        ["a", "b", "c"] ->
            tree["a"]["b"]["c"] = {}
    """
    current = tree
    for part in parts:
        current = current.setdefault(part, {})

def print_tree(tree, indent=0):
    """
    Recursively prints tree structure
    """
    lines = []
    for key in sorted(tree.keys()):
        line = "  " * indent + key + "/"
        lines.append(line)
        lines.extend(print_tree(tree[key], indent + 1))
    return lines

# -------------------------------
# Pagination
# -------------------------------
paginator = s3.get_paginator("list_object_versions")

pagination_args = {
    "Bucket": S3_BUCKET_NAME
}

if S3_BUCKET_PREFIX:
    pagination_args["Prefix"] = S3_BUCKET_PREFIX

for page in paginator.paginate(**pagination_args):

    if "Versions" in page:
        for v in page["Versions"]:
            key = v["Key"]
            object_history.setdefault(key, []).append({
                "Type": "version",
                "VersionId": v["VersionId"],
                "LastModified": v["LastModified"]
            })

    if "DeleteMarkers" in page:
        for d in page["DeleteMarkers"]:
            key = d["Key"]
            object_history.setdefault(key, []).append({
                "Type": "delete",
                "VersionId": d["VersionId"],
                "LastModified": d["LastModified"]
            })

# -------------------------------
# Resolve state at target time
# -------------------------------
existing_folder_keys = []

for key, events in object_history.items():

    if not key.endswith("_$folder$"):
        continue

    valid_events = [e for e in events if e["LastModified"] <= target_dt]
    if not valid_events:
        continue

    valid_events.sort(key=lambda x: x["LastModified"])
    latest = valid_events[-1]

    if latest["Type"] == "delete":
        continue

    existing_folder_keys.append(clean_string(key))

# -------------------------------
# Build hierarchical tree
# -------------------------------
tree = {}

for key in existing_folder_keys:
    # Remove suffix and split path
    path = key.replace("_$folder$", "")
    parts = [p for p in path.split("/") if p]

    if parts:
        insert_into_tree(tree, parts)

# -------------------------------
# Output tree
# -------------------------------
tree_lines = print_tree(tree)

print("\n--- Folder Tree ---\n")
for line in tree_lines:
    print(line)

# -------------------------------
# Save outputs
# -------------------------------
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# Save tree
tree_file = f"folder_tree_{timestamp}.txt"
with open(tree_file, "w", encoding="utf-8") as f:
    f.write("\n".join(tree_lines))

# Save CSV (optional flat list)
csv_file = f"folder_list_{timestamp}.csv"
with open(csv_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Key"])
    for k in sorted(existing_folder_keys):
        writer.writerow([k])

print(f"\nSaved tree to {tree_file}")
print(f"Saved flat list to {csv_file}")
print(f"Total folders: {len(existing_folder_keys)}")