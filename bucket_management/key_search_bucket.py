import csv
import os
import mimetypes
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
import dotenv

# Load .env file
dotenv.load_dotenv()

# AWS credentials and bucket info
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_S3_ENDPOINT = os.getenv("AWS_S3_ENDPOINT")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")

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

# Prepare CSV output file name with timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = f"object_report_{timestamp}.csv"

# CSV headers
headers = ["Key", "Size (KB)", "File Type", "Created Date", "Last Modified Date", "Deleted Date"]

def get_file_type(key, content_type):
    # If ContentType exists, use it
    if content_type and content_type.strip():
        return content_type
    # Otherwise, infer from file extension
    type_guess, _ = mimetypes.guess_type(key)
    return type_guess if type_guess else "unknown"

rows = []
for key in object_keys:
    try:
        versions = s3_client.list_object_versions(Bucket=AWS_S3_BUCKET, Prefix=key)
        version_list = versions.get("Versions", [])
        delete_markers = versions.get("DeleteMarkers", [])

        if not version_list and not delete_markers:
            rows.append([key, "", "", "", "", ""])
            continue

        version_list.sort(key=lambda v: v["LastModified"])
        created_date = version_list[0]["LastModified"].strftime("%Y-%m-%d %H:%M:%S") if version_list else ""
        last_modified_date = version_list[-1]["LastModified"].strftime("%Y-%m-%d %H:%M:%S") if version_list else ""
        size_kb = round(version_list[-1]["Size"] / 1024, 2) if version_list else ""

        # Try to get ContentType from head_object
        content_type = ""
        try:
            head = s3_client.head_object(Bucket=AWS_S3_BUCKET, Key=key)
            content_type = head.get("ContentType", "")
        except ClientError:
            pass

        file_type = get_file_type(key, content_type)

        deletion_date = ""
        if delete_markers:
            delete_markers.sort(key=lambda d: d["LastModified"])
            deletion_date = delete_markers[-1]["LastModified"].strftime("%Y-%m-%d %H:%M:%S")

        rows.append([key, size_kb, file_type, created_date, last_modified_date, deletion_date])

    except ClientError as e:
        rows.append([key, "Error", str(e), "", "", ""])

# Write to CSV
with open(output_file, "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(headers)
    writer.writerows(rows)

print(f"Report generated: {output_file}")
