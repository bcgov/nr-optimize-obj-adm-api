from boto3 import client, resource
from botocore.exceptions import ClientError
from constants import BUCKET_NAME
from utilities.log_helper import LOGGER
from boto3_helpers.searches import get_filenames_complex

# Returns true if the bucket exists
def bucket_exists(s3: resource, bucket_name: str = BUCKET_NAME) -> bool:
    s3_bucket = s3.Bucket(bucket_name)

    bucket_exists = s3_bucket.creation_date is not None
    LOGGER.info(f"Bucket {bucket_name} exists? {bucket_exists}")
    return bucket_exists

# Returns true if there's an exact file name match in object storage
def object_exists(s3_client: client, file_name: str, bucket_name: str = BUCKET_NAME) -> bool:
    try:
        s3_client.head_object(Bucket=bucket_name, Key=file_name)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        else:
            LOGGER.info(f"Error occurred while checking if file {file_name} exists in bucket {bucket_name}: {e}")
            # Something else has gone wrong.
            raise

# Returns true if uppercase files exist in an object storage bucket
def uppercase_files_exist(s3_resource: resource, bucket_name: str = BUCKET_NAME) -> bool:
    if not bucket_exists(s3_resource, bucket_name=bucket_name):
        LOGGER.error(f"Bucket {bucket_name} does not exist.")
        raise Exception(f"Bucket {bucket_name} does not exist.")

    result = get_filenames_complex(s3_resource, file_path=None, bucket_name=bucket_name, uppercase_only=True, prefix=None, max = 1)
    return result > 0