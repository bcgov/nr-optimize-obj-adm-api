import boto3
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

# Generate timestamp
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

# Convert to datetime with UTC timezone
start_date = datetime.strptime(start_input, "%Y-%m-%d").replace(tzinfo=timezone.utc)
end_date = datetime.strptime(end_input, "%Y-%m-%d").replace(tzinfo=timezone.utc)


# Initialize S3 client
s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    endpoint_url=AWS_S3_ENDPOINT
)

restored_objects = []
failed_objects = []

# Paginate through object versions
paginator = s3.get_paginator('list_object_versions')
for page in paginator.paginate(Bucket=AWS_S3_BUCKET):
    if 'DeleteMarkers' in page:
        for marker in page['DeleteMarkers']:
            last_modified = marker['LastModified']
            if start_date <= last_modified <= end_date:
                key = marker['Key']
                version_id = marker['VersionId']
                try:
                    # Remove delete marker to restore object
                    s3.delete_object(
                        Bucket=AWS_S3_BUCKET,
                        Key=key,
                        VersionId=version_id
                    )
                    restored_objects.append(f"Restored: {key} | versionId={version_id} | deleted_at={last_modified.isoformat()}")
                except Exception as e:
                    failed_objects.append(f"Failed: {key} | versionId={version_id} | error={str(e)}")

# Write log file
with open("restore-log_{timestamp}.txt", "w") as log:
    log.write("Restoration Summary\n")
    log.write("="*50 + "\n")
    log.write(f"Total restored: {len(restored_objects)}\n")
    log.write(f"Total failed: {len(failed_objects)}\n\n")

    log.write("Restored Objects:\n")
    log.write("\n".join(restored_objects) + "\n\n")

    if failed_objects:
        log.write("Failed Objects:\n")
        log.write("\n".join(failed_objects) + "\n")

print(f"Restoration complete. Restored {len(restored_objects)} objects. Log saved to restore-log.txt.")