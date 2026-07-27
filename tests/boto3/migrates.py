from tests.boto3.auth import test_get_resource
from boto3_helpers.checks import bucket_exists, object_exists
from boto3_helpers.deletes import hard_delete_objects
from boto3_helpers.migrates import move_object
from boto3_helpers.metadata import get_object_size
from botocore.exceptions import ClientError
from constants import TEMP_DIR
from tests.constants import BUCKET_NAME, TEST_FILE_PATH
from utilities.log_helper import LOGGER
from utilities.file_helper import delete_file
import os

def test_move_object(s3_resource):
    # Generate an improbable test file to use
    temp_test_file_name = "temp-test-file-for-automated-testing.txt"
    temp_test_file_new_name = "temp-test-file-for-automated-testing-new.txt"
    try:         
        assert bucket_exists(s3_resource, bucket_name=BUCKET_NAME) is True
        s3_client = s3_resource.meta.client        
        
        # Get info for the test file to be moved
        assert os.path.exists(TEST_FILE_PATH) is True

        # Add the test file to the bucket
        try:
            s3_client.upload_file(
                Filename=TEST_FILE_PATH,
                Bucket=BUCKET_NAME,
                Key=temp_test_file_name
            )
            LOGGER.info("Upload test file successful!")
            assert object_exists(s3_client, temp_test_file_name, BUCKET_NAME) is True
        except ClientError as e:
            LOGGER.error(f"Error uploading file: {e}")
            raise
        
        # Move
        move_success = move_object(s3_client, temp_test_file_name, temp_test_file_new_name, BUCKET_NAME, BUCKET_NAME)
        assert move_success is True

        # Size comparison
        test_file_size = os.path.getsize(TEST_FILE_PATH)
        new_object_size = get_object_size(s3_client, temp_test_file_new_name, BUCKET_NAME)
        assert test_file_size == new_object_size

        # Confirm file Moved
        assert object_exists(s3_client, temp_test_file_name, BUCKET_NAME) is False
        assert object_exists(s3_client, temp_test_file_new_name, BUCKET_NAME) is True

        # Clean Up
        hard_delete_objects(s3_client, [temp_test_file_name,temp_test_file_new_name], BUCKET_NAME)

    except Exception as e:
        LOGGER.error(f"Error occurred in test_move_object: {e}")


s3_resource = test_get_resource()
test_move_object(s3_resource)