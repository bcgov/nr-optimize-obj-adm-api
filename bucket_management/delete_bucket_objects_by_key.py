import boto3
from botocore.exceptions import ClientError
import dotenv
import os
import csv
from datetime import datetime

# Dry-run mode: True means no actual deletion, just report
DRY_RUN = True

# Load .env file
dotenv.load_dotenv()

# AWS credentials and bucket info
ACCESS_KEY = os.getenv("ACCESS_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
S3_ENDPOINT = os.getenv("S3_ENDPOINT")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

# Validate environment variables
if not all([ACCESS_KEY, SECRET_KEY, S3_ENDPOINT, S3_BUCKET_NAME]):
    raise ValueError("Missing required AWS environment variables in .env file.")

# Read object keys from os_keys.txt
with open("os_keys.txt", "r") as f:
    object_keys = [line.strip() for line in f if line.strip()]

# Initialize boto3 S3 client
s3_client = boto3.client(
    "s3",
    ACCESS_KEY=ACCESS_KEY,
    SECRET_KEY=SECRET_KEY,
    endpoint_url=S3_ENDPOINT
)

deleted = []
skipped = []

# If dry-run, show what would be deleted and prompt user
if DRY_RUN:
    print("Dry-Run Mode: The following objects would be deleted:")
    for key in object_keys:
        print(f" - {key}")
    confirm = input("Do you want to proceed with actual deletion? (Y/N): ").strip().lower()
    if confirm == "y":
        DRY_RUN = False
        print("Proceeding with actual deletion...")
    else:
        print("Aborting deletion. No changes made.")

for key in object_keys:
    try:
        if DRY_RUN:
            skipped.append((key, "Dry-Run", "No deletion performed"))
        else:
            # Perform soft delete (adds delete marker if versioning enabled)
            s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=key)
            deleted.append((key, "Deleted", ""))
    except ClientError as e:
        skipped.append((key, "Skipped", f"Delete failed: {e}"))

# Prepare CSV output file name with timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = f"delete_report_{timestamp}.csv"

# Write to CSV
with open(output_file, "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Key", "Status", "Reason"])
    for key, status, reason in deleted + skipped:
        writer.writerow([key, status, reason])

# Print summary
print("Delete Summary:")
print(f"Dry-Run mode: {DRY_RUN}")
print(f"Deleted objects ({len(deleted)}): {[k for k, _, _ in deleted]}")
print(f"Reported objects ({len(skipped)}): {[k for k, _, _ in skipped]}")
print(f"Report saved to {output_file}")