
import boto3
from constants import BUCKET_NAME
from utilities.log_helper import LOGGER

# The client is a low-level service client that provides methods for interacting with AWS services.
# It allows you to make API calls to AWS services pretty much directly.
def move_object(s3_client, source_path: str, dest_path: str, source_bucket_name: str = BUCKET_NAME, destination_bucket_name: str = BUCKET_NAME):
    
    # Copy
    try:
        LOGGER.debug(f"Copying {source_path}")
        s3_client.copy(
            CopySource={"Bucket": source_bucket_name, "Key": source_path},
            Bucket=destination_bucket_name,
            Key=dest_path    
        )
        LOGGER.debug(f"Copy successful. Deleting source.")
        try: 
            s3_client.delete_object(Bucket=source_bucket_name, Key=source_path)
            LOGGER.debug(f"Delete successful.")    
            return True
        except Exception as e:
            LOGGER.error(f"Failed to delete file: {source_path}. Error: {e}")
            raise

 
    except Exception as e:
        LOGGER.error(f"Failed to copy file: {source_path}. Error: {e}")
        raise


