import boto3
from botocore.config import Config
import getpass
import logging

def setup_logging(log_path):
    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def main():
    # Setup logging
    log_path = r'C:\Git_Repo\nr-optimize-obj-adm-api\ecs_cleanup.log'
    setup_logging(log_path)

    # Prompt for credentials and bucket info
    access_key = input("Enter your Access Key: ")
    secret_key = getpass.getpass("Enter your Secret Key: ")
    bucket_name = input("Enter the Bucket Name: ")

    # Connect to ECS
    session = boto3.session.Session()
    s3 = session.client(
        service_name='s3',
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        endpoint_url='https://nrs.objectstore.gov.bc.ca:443',
        config=Config(signature_version='s3v4')
    )

    try:
        paginator = s3.get_paginator('list_object_versions')
        page_iterator = paginator.paginate(Bucket=bucket_name)

        file_versions = {}

        # Collect versions grouped by file key
        for page in page_iterator:
            versions = page.get('Versions', [])
            for v in versions:
                key = v['Key']
                if key not in file_versions:
                    file_versions[key] = []
                file_versions[key].append(v)

        # Process each file
        for key, versions in file_versions.items():
            versions.sort(key=lambda x: x['LastModified'], reverse=True)
            to_delete = versions[5:]

            if not to_delete:
                logging.info(f"No versions to delete for '{key}'.")
                continue

            delete_objects = {
                'Objects': [{'Key': key, 'VersionId': v['VersionId']} for v in to_delete],
                'Quiet': True
            }

            try:
                response = s3.delete_objects(Bucket=bucket_name, Delete=delete_objects)
                deleted = response.get('Deleted', [])
                for d in deleted:
                    logging.info(f"Deleted version {d['VersionId']} of '{d['Key']}'")
            except Exception as e:
                logging.error(f"Error deleting versions for '{key}': {str(e)}")

    except Exception as e:
        logging.error(f"Error accessing bucket '{bucket_name}': {str(e)}")

if __name__ == "__main__":
    main()
