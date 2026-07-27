from tests.boto3.auth import test_get_resource
from boto3_helpers.checks import bucket_exists, object_exists, uppercase_files_exist
from tests.constants import ACCESS_KEY, SECRET_KEY, BUCKET_NAME, TEST_FILE_PATH
from utilities.log_helper import LOGGER

def test_bucket_exists(s3_resource):
    try: 
        assert bucket_exists(s3_resource, bucket_name=BUCKET_NAME) is True
        assert bucket_exists(s3_resource, bucket_name="A-random-bucket-that-does-not-exist") is False
    except Exception as e:
        LOGGER.error(f"Error occurred in test_bucket_exists: {e}")
    
def test_file_exists(s3_client):
    try: 
        object_exists_result = object_exists(s3_client, file_name=TEST_FILE_PATH, bucket_name=BUCKET_NAME)
        assert object_exists_result is True
        object_exists_result = object_exists(s3_client, file_name="A-random-file-that-does-not-exist", bucket_name=BUCKET_NAME)
        assert object_exists_result is False
    except Exception as e:
        LOGGER.error(f"Error occurred in test_file_exists: {e}")

def test_uppercase_files_exist(s3_resource):
    try: 
        uppercase_files_exist_result = uppercase_files_exist(s3_resource, bucket_name=BUCKET_NAME)
        assert isinstance(uppercase_files_exist_result, bool)
    except Exception as e:
        LOGGER.error(f"Error occurred in test_uppercase_files_exist: {e}")

new_resource = test_get_resource()
test_bucket_exists(new_resource)
test_file_exists(new_resource.meta.client)
test_uppercase_files_exist(new_resource)