from boto3_helpers.checks import bucket_exists, object_exists
from boto3_helpers.deletes import soft_delete_object, soft_delete_objects, hard_delete_object, hard_delete_objects, delete_excessive_versions
from boto3_helpers.searches import get_all_version_counts
from botocore.exceptions import ClientError
from tests.boto3.auth import test_get_resource
from tests.constants import BUCKET_NAME, TEST_FILE_PATH
from utilities.log_helper import LOGGER

# Tests both soft and hard single file deletes
def test_delete_object(s3_client):
    try: 
        # Generate multiple versions of an improbable test file to use
        temp_test_object_name = "temp-test-file-for-automated-testing.txt"
        for _ in range(3):
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
    

    # Soft delete it
    soft_delete_object(s3_client, temp_test_object_name, BUCKET_NAME)

    # Confirm the soft delete
    assert object_exists(s3_client, temp_test_object_name, BUCKET_NAME) is False

    # Confirm the previous versions exist
    result = get_all_version_counts(s3_client, BUCKET_NAME, temp_test_object_name)
    version_count = result[temp_test_object_name]
    assert version_count > 0

    # Hard delete it
    hard_delete_object(s3_client, temp_test_object_name, BUCKET_NAME)

    # Confirm the previous versions exist
    result = get_all_version_counts(s3_client, BUCKET_NAME, temp_test_object_name)
    assert temp_test_object_name not in result

# Tests both soft and hard mutli file deletes
def test_delete_objects(s3_client):

    # Generate multiple versions of an improbable test file to use
    temp_test_object_name = "temp-test-file-for-automated-testing.txt"
    temp_test_object_name2 = "temp-test-file-for-automated-testing-2.txt"
    temp_object_names = [temp_test_object_name,temp_test_object_name2]
    try: 
        for _ in range(4):
            for name in temp_object_names:
                s3_client.upload_file(
                    Filename=TEST_FILE_PATH,
                    Bucket=BUCKET_NAME,
                    Key=name
                )
                assert object_exists(s3_client, name, BUCKET_NAME) is True
        LOGGER.debug("Uploaded test files successful!")

    except ClientError as e:
        LOGGER.error(f"Error uploading files: {e}")
        raise
    

    # Soft delete them
    soft_delete_objects(s3_client, temp_object_names, BUCKET_NAME)

    for name in temp_object_names:
        # Confirm the soft deletes
        assert object_exists(s3_client, name, BUCKET_NAME) is False

        # Confirm the previous versions exist
        result = get_all_version_counts(s3_client, BUCKET_NAME, name)
        version_count = result[name]
        assert version_count > 0

    # Delete excessive versions
    delete_excessive_versions(s3_client, temp_object_names, max_version_count=1, bucket=BUCKET_NAME)
    # Confirm new count is correct
    for name in temp_object_names:
        result = get_all_version_counts(s3_client, BUCKET_NAME, name)
        version_count = result[name]
        assert version_count == 1


    # Hard delete them
    hard_delete_objects(s3_client, temp_object_names, BUCKET_NAME)


    for name in temp_object_names:
        # Confirm the previous versions exist
        result = get_all_version_counts(s3_client, BUCKET_NAME, name)
        assert name not in result

new_resource = test_get_resource()
s3_client = new_resource.meta.client
# test_delete_object(s3_client)
test_delete_objects(s3_client)

