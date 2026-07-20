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
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    endpoint_url=S3_ENDPOINT
)

# Prepare CSV output file name with timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = f"object_report_{timestamp}.csv"

# Create downloads folder if not exists
download_folder = "downloads"
os.makedirs(download_folder, exist_ok=True)

# CSV headers
headers = ["Key", "Size (KB)", "File Type", "Created Date", "Last Modified Date", "Deleted Date"]

def get_file_type(key, content_type):
    if content_type and content_type.strip():
        return content_type
    type_guess, _ = mimetypes.guess_type(key)
    return type_guess if type_guess else "unknown"

rows = []
for key in object_keys:
    try:
        versions = s3_client.list_object_versions(Bucket=S3_BUCKET_NAME, Prefix=key)
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
            head = s3_client.head_object(Bucket=S3_BUCKET_NAME, Key=key)
            content_type = head.get("ContentType", "")
        except ClientError:
            pass

        file_type = get_file_type(key, content_type)

        deletion_date = ""
        if delete_markers:
            delete_markers.sort(key=lambda d: d["LastModified"])
            deletion_date = delete_markers[-1]["LastModified"].strftime("%Y-%m-%d %H:%M:%S")

        # Determine which version to download
        download_version = None
        if delete_markers and delete_markers[-1]["IsLatest"]:
            # Latest is a delete marker, pick previous non-deleted version
            non_deleted_versions = [v for v in version_list if not v.get("IsDeleteMarker", False)]
            if non_deleted_versions:
                download_version = non_deleted_versions[-1]  # most recent non-deleted
        else:
            # Latest version is not deleted
            download_version = version_list[-1]

        # Download the chosen version if available
        if download_version:
            try:
                download_path = os.path.join(download_folder, key)
                s3_client.download_file(
                    S3_BUCKET_NAME,
                    key,
                    download_path,
                    ExtraArgs={"VersionId": download_version["VersionId"]}
                )
            except ClientError as e:
                print(f"Failed to download {key}: {e}")
        else:
            print(f"No downloadable version found for {key}")

        rows.append([key, size_kb, file_type, created_date, last_modified_date, deletion_date])

    except ClientError as e:
        rows.append([key, "Error", str(e), "", "", ""])

# Write to CSV
with open(output_file, "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(headers)
    writer.writerows(rows)

print(f"Report generated: {output_file}")
print(f"Downloaded files are in '{download_folder}' folder.")