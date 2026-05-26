# -------------------------------------------------------------------------------
# Name:        upload_folder.py
# Purpose:     Quick demo of uploading folder contents from windows to object storage bucket.
#
# Author:      PPLATTEN
#
# Created:     2026-03-20
# -------------------------------------------------------------------------------

import os
import sys

from minio import Minio
from minio.error import S3Error
from constants import S3_ENDPOINT, OBJSTOR_ENDPOINT, S3_BUCKET_NAME, ACCESS_KEY, SECRET_KEY

# update to be the directory
upload_directory = "C:\\Temp\\temp"

print(ACCESS_KEY)
print(S3_ENDPOINT)
print(OBJSTOR_ENDPOINT)
print(S3_BUCKET_NAME)

# copy a file to bucket
def copy_to_bucket(minio_client, file_name):
    print("copying to bucket: ", file_name)

    # upload file
    minio_client.fput_object(
        S3_BUCKET_NAME,
        file_name,
        os.path.join(upload_directory, file_name.lower()),
    )
    return

def main(argv):

    minio_client = Minio(
        endpoint=OBJSTOR_ENDPOINT,
        access_key=ACCESS_KEY,
        secret_key=SECRET_KEY,
        region="US",
    )

    # add pvc file names and last modified timestamp to comparison dictionary
    for dirname, dirnames, filenames in os.walk(upload_directory):
        
        # print path to all filenames.
        for file_name in filenames:
            print(file_name)
            
            copy_to_bucket(minio_client, file_name)           


if __name__ == "__main__":
    try:
        print("Starting copy...")
        main(sys.argv[1:])
        print("Copy finished.")
    except S3Error as exc:
        print("error occurred.", exc)
