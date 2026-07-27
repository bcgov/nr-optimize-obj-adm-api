from boto3 import client, resource
from botocore.exceptions import ClientError
from constants import BUCKET_NAME
from utilities.log_helper import LOGGER
from typing import List

# Adds delete marker to an object, recoverable
# Returns true if the file deleted
def soft_delete_object(s3_client, object_path: str, bucket_name: str = BUCKET_NAME) -> bool:

    try:
        s3_client.delete_object(
            Bucket=bucket_name,
            Key=object_path
        )
        LOGGER.info(f"Deletion successful for: {object_path}")
        return True
    except ClientError as e:
        LOGGER.error(f"Failed to delete object: {e}")
    return False

# Adds delete marker to objects, recoverable
def soft_delete_objects(s3_client, object_paths: List[str], bucket_name: str = BUCKET_NAME) -> bool:
    try:
        s3_client.delete_objects(
            Bucket=bucket_name,
            Delete={
                'Objects': [{'Key': path} for path in object_paths],
                'Quiet': True
            }
        )
    except ClientError as e:
        LOGGER.error(f"Failed to delete object: {e}")
    return False

# Permanently delete an object and its previous versions
# Returns true if the file deleted
def hard_delete_object(s3_client, object_path: str, bucket_name: str = BUCKET_NAME) -> bool:
    hard_delete_objects(s3_client, [object_path], bucket_name)

# Permanently delete a list of objects and their previous versions
# Returns a list of successfully deleted objects
def hard_delete_objects(s3_client, object_paths: List[str], bucket_name: str = BUCKET_NAME):
    versions_paginator = s3_client.get_paginator('list_object_versions')
    
    objects_deleted = []

    for object_path in object_paths:
        # Track items to remove
        versions_to_delete = []
        
        # 1. Fetch all historical versions of the object
        for page in versions_paginator.paginate(Bucket=bucket_name, Prefix=object_path):
            # Add normal object versions
            for version in page.get('Versions', []):
                if version['Key'] == object_path:
                    versions_to_delete.append({
                        'Key': version['Key'],
                        'VersionId': version['VersionId']
                    })
            
            # Add any soft delete markers that were previously created
            for marker in page.get('DeleteMarkers', []):
                if marker['Key'] == object_path:
                    versions_to_delete.append({
                        'Key': marker['Key'],
                        'VersionId': marker['VersionId']
                    })
                    
        # 2. Perform the permanent hard deletion in batches if versions exist
        if versions_to_delete:
            # Data Center has a version limit of 500 per object so no need to paginate
            response = s3_client.delete_objects(
                Bucket=bucket_name,
                Delete={'Objects': versions_to_delete}
            )
            LOGGER.info(f"Successfully permanently deleted {len(versions_to_delete)} version items for {object_path}.")
            objects_deleted.append(object_path)
        else:
            LOGGER.info("No object versions or delete markers found matching that key.")
    return objects_deleted

def delete_excessive_versions(s3_client, object_paths: List[str], max_version_count: int = 50, bucket:str = BUCKET_NAME):
     # for each object with over maximum_versions
    for line in object_paths:
        # get all versions of that object
        result = s3_client.list_object_versions(Bucket=BUCKET_NAME,Prefix=line)

        # Get the specific version ids
        delete_objects=[]
        counter = 0
        for item in result["Versions"]:
            if counter < max_version_count:
                counter+=1
                continue
            # after skipping the allowed versions, create dict of versions to delete
            delete_objects.append({"Key":line,"VersionId":item["VersionId"]})

        # Delete unwanted versions
        LOGGER.debug(f"Deleting {len(delete_objects)} from {line}")
        result = s3_client.delete_objects(Bucket=BUCKET_NAME,Delete={'Objects': delete_objects})
        LOGGER.debug(f"Deleted {len(result['Deleted'])} from {line}")