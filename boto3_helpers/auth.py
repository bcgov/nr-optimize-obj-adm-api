import boto3
from constants import S3_ENDPOINT, ACCESS_KEY, SECRET_KEY
from utilities.log_helper import LOGGER

# The client is a low-level service client that provides methods for interacting with AWS services.
# It allows you to make API calls to AWS services pretty much directly.
def get_client(access_key: str = ACCESS_KEY, secret_key: str = SECRET_KEY):
    try:
        client = boto3.client(
            "s3",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            endpoint_url=S3_ENDPOINT,
        )
        return client
    except Exception as e:
        LOGGER.info(f"Error occurred while creating S3 client: {e}")
        return None

# The resource is a higher-level abstraction that provides an object-oriented interface to AWS services.
def get_resource(access_key: str = ACCESS_KEY, secret_key: str = SECRET_KEY):
    try:
        s3_resource = boto3.resource(
            "s3",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            endpoint_url=S3_ENDPOINT,
        )
        return s3_resource
    except Exception as e:
        LOGGER.info(f"Error occurred while creating S3 resource: {e}")
        return None