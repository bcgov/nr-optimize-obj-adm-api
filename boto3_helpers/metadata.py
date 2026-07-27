from botocore.exceptions import ClientError
from constants import BUCKET_NAME
from utilities.log_helper import LOGGER

def get_object_metadata(s3_client, object_path: str, bucket_name: str = BUCKET_NAME):

    try:
        response = s3_client.head_object(
            Bucket=bucket_name,
            Key=object_path
        )

        LOGGER.debug(f"Metadata retrieved for: {object_path}")
        return response
    except ClientError as e:
        LOGGER.error(f"Failed to delete object: {e}")
        raise


# Returns the size of an object efficiently
def get_object_size(s3_client, object_path: str, bucket_name: str = BUCKET_NAME) -> int:
    response = get_object_metadata(s3_client, object_path, bucket_name)
    return response['ContentLength']