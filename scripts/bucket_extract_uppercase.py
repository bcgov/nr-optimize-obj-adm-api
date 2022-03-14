# -------------------------------------------------------------------------------
# Name:        bucket_extract_uppercase.py
# Purpose:     the purpose of the script is to scan an object storage bucket for uppercase
#              filenames and write them (if any) to a text document for review :
#              1.) you will need an .env file for key/value pairs and a constant.py file to successfully run this script
#              2.) connect to S3 Object Storage bucket
#              3.) read object keys to list
#              4.) iterate over list, write filenames containing uppercase to file
#
# Author:      HHAY, PPLATTEN
#
# Created:     2022-03-13
# Copyright:   (c) OPTIMIZATION TEAM 2022
# Licence:     mine
#
#
# usage: 'bucket_extract_uppercase.py
# example: 'bucket_extract_uppercase.py'
# -------------------------------------------------------------------------------

import boto3
import constant
import sys
from minio.error import S3Error


def main():
    obj = []
    bucket = constant.AWS_S3_BUCKET

    # Create a resource with S3, it's access key, secret key, and public endpoint.
    s3 = boto3.resource(
        "s3",
        aws_access_key_id=constant.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=constant.AWS_SECRET_ACCESS_KEY,
        endpoint_url=constant.AWS_S3_ENDPOINT,
    )

    s3_bucket = s3.Bucket(bucket)

    # Check that bucket exists.
    if s3_bucket.creation_date is None:
        print("Bucket {} does not exist.".format(bucket))
        sys.exit()
    else:
        print(
            "Bucket {} exists. \n Parsing object keys for uppercase...\n".format(bucket)
        )

    # parse bucket object keys for files with uppercase letters & write to file
    with open("{}_extract_uppercase.txt".format(bucket), "w") as f:
        for s3_bucket_object in s3_bucket.objects.all():
            obj = s3_bucket_object.key
            if obj.isupper():
                f.write(obj)
                f.write("\n")


if __name__ == "__main__":
    try:
        main()
    except S3Error as exc:
        print("error occurred.", exc)
