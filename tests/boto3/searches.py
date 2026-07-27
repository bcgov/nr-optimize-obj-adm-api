from tests.boto3.auth import test_get_resource
from boto3_helpers.checks import bucket_exists, object_exists
from boto3_helpers.searches import save_all_filenames, get_all_filenames, save_uppercase_filenames, get_all_version_counts
from boto3_helpers.deletes import hard_delete_object
from botocore.exceptions import ClientError
from constants import TEMP_DIR
from tests.constants import BUCKET_NAME, TEST_FILE_PATH
from utilities.log_helper import LOGGER
from utilities.file_helper import delete_file
import os

def test_save_all_filenames(s3_resource):
    try:         
        assert bucket_exists(s3_resource, bucket_name=BUCKET_NAME) is True
        
        # Create a temporary file path for testing
        TEMP_FILE_PATH = os.path.join(TEMP_DIR, f"{BUCKET_NAME}_all_filenames.txt")

        # Download the data
        result = save_all_filenames(s3_resource, file_path=TEMP_FILE_PATH, bucket_name=BUCKET_NAME, prefix=None)
        assert isinstance(result, int)
        assert result >= 0

        # test file exists and has content
        assert os.path.exists(TEMP_FILE_PATH) is True
        assert os.path.getsize(TEMP_FILE_PATH) > 0

        delete_file(TEMP_FILE_PATH)
    except Exception as e:
        LOGGER.error(f"Error occurred in test_save_all_filenames: {e}")

def test_get_all_filenames(s3_resource):
    try:
        assert bucket_exists(s3_resource, bucket_name=BUCKET_NAME) is True

        result = get_all_filenames(s3_resource, bucket_name=BUCKET_NAME, prefix=None)
        assert isinstance(result, list)
        assert len(result) >= 0
    except Exception as e:
        LOGGER.error(f"Error occurred in test_get_all_filenames: {e}")

def test_save_uppercase_filenames(s3_resource):
    try:         
        assert bucket_exists(s3_resource, bucket_name=BUCKET_NAME) is True
        
        # Create a temporary file path for testing
        TEMP_FILE_PATH = os.path.join(TEMP_DIR, f"{BUCKET_NAME}_all_uppercase_filenames.txt")

        # Download the data
        result = save_uppercase_filenames(s3_resource, file_path=TEMP_FILE_PATH, bucket_name=BUCKET_NAME, prefix=None)
        assert isinstance(result, int)
        assert result >= 0

        # test file exists and has content
        assert os.path.exists(TEMP_FILE_PATH) is True
        assert os.path.getsize(TEMP_FILE_PATH) > 0

        # test that output file has only paths which contain uppercase letters
        found_line_without_uppercase = False
        with open(TEMP_FILE_PATH, "r", encoding="utf-8") as file:
            for line in file:
                # Check if there is NO uppercase letter in the current line
                if not any(char.isupper() for char in line):
                    found_line_without_uppercase = True
        assert found_line_without_uppercase is False

        # Clean up
        delete_file(TEMP_FILE_PATH)
    except Exception as e:
        LOGGER.error(f"Error occurred in test_save_all_filenames: {e}")

def test_get_all_version_counts(s3_client):

    # Generate an improbable test file to use
    temp_test_object_name = "temp-test-file-for-automated-testing.txt"
 
    assert bucket_exists(s3_resource, bucket_name=BUCKET_NAME) is True
    s3_client = s3_resource.meta.client        
    
    # Get info for the test file to be moved
    assert os.path.exists(TEST_FILE_PATH) is True

    # Add the test file to the bucket
    try:
        # Upload a test file twice to create a noncurrent version
        for _ in range(2):
            s3_client.upload_file(
                Filename=TEST_FILE_PATH, 
                Bucket=BUCKET_NAME,
                Key=temp_test_object_name
            )
        LOGGER.debug("Upload test files successful!")

        assert object_exists(s3_client, temp_test_object_name, BUCKET_NAME) is True
    except ClientError as e:
        LOGGER.error(f"Error uploading files: {e}")
        raise
    
    result = get_all_version_counts(s3_client, BUCKET_NAME, temp_test_object_name)
    assert result[temp_test_object_name] > 1
    hard_delete_object(s3_client, temp_test_object_name, BUCKET_NAME)
    result = get_all_version_counts(s3_client, bucket = BUCKET_NAME, prefix=temp_test_object_name)
    assert result[temp_test_object_name] == 0




s3_resource = test_get_resource()
s3_client = s3_resource.meta.client
# test_save_all_filenames(s3_resource)
# test_get_all_filenames(s3_resource)
# test_save_uppercase_filenames(s3_resource)
test_get_all_version_counts(s3_client)