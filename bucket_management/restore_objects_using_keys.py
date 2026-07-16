import boto3
from botocore.exceptions import ClientError
import dotenv
import os
import csv
from datetime import datetime

# Load .env file
dotenv.load_dotenv()

# AWS credentials and bucket info
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_S3_ENDPOINT = os.getenv("AWS_S3_ENDPOINT")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")

# Validate environment variables
if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_S3_ENDPOINT, AWS_S3_BUCKET]):
    raise ValueError("Missing required AWS environment variables in .env file.")

# Read object keys from os_keys.txt
with open("os_keys.txt", "r") as f:
    object_keys = [line.strip() for line in f if line.strip()]

# Initialize boto3 S3 client
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    endpoint_url=AWS_S3_ENDPOINT
)

restored = []
skipped = []

for key in object_keys:
    try:
        # Get all versions of the object
        versions = s3_client.list_object_versions(Bucket=AWS_S3_BUCKET, Prefix=key)
        version_list = versions.get("Versions", [])

        if not version_list:
            skipped.append((key, "Skipped", "No non-deleted versions found"))
            continue

        # Sort versions by LastModified
        version_list.sort(key=lambda v: v["LastModified"])

        # Find the most recent non-deleted version
        non_deleted_versions = [v for v in version_list if not v.get("IsDeleteMarker", False)]
        if not non_deleted_versions:
            skipped.append((key, "Skipped", "All versions are delete markers"))
            continue

        latest_non_deleted = non_deleted_versions[-1]
        version_id = latest_non_deleted["VersionId"]

        # Restore by copying this version to the same key (creates a new latest version)
        try:
            s3_client.copy_object(
                Bucket=AWS_S3_BUCKET,
                CopySource={"Bucket": AWS_S3_BUCKET, "Key": key, "VersionId": version_id},
                Key=key
            )
            restored.append((key, "Restored", ""))
        except ClientError as e:
            skipped.append((key, "Skipped", f"Restore failed: {e}"))

    except ClientError as e:
        skipped.append((key, "Skipped", f"Error retrieving versions: {e}"))

# Prepare CSV output file name with timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = f"restore_report_{timestamp}.csv"

# Write to CSV
with open(output_file, "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Key", "Status", "Reason"])
    for key, status, reason in restored + skipped:
        writer.writerow([key, status, reason])

# Print summary
print("Restore Summary:")
print(f"Restored objects ({len(restored)}): {[k for k, _, _ in restored]}")
print(f"Skipped objects ({len(skipped)}): {[k for k, _, _ in skipped]}")
