# -------------------------------------------------------------------------------
# Name:        modify_bucket_policy.py
# Purpose:     the purpose of the script is to provide programmatic options to:
#              - create an object storage bucket policy
#              - list an object storage bucket policy
#              - delete an object storage bucket policy
#              1.) you will need an .env file for key/value pairs and a constant.py file to successfully run this script
#              2.) connect to S3 Object Storage bucket
#
# Author:      HHAY, PPLATTEN
#
# Created:     2023-11-20
# Copyright:   (c) OPTIMIZATION TEAM 2023
# Licence:     mine
#
#
# usage: 'modify_bucket_policy.py
# example: 'modify_bucket_policy.py'
# -------------------------------------------------------------------------------

# import python libraries
import boto3
import constants
import json


# create a client with S3, the access key, secret key, and public endpoint.
s3_client = boto3.client(
    "s3",
    aws_access_key_id=constants.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=constants.AWS_SECRET_ACCESS_KEY,
    endpoint_url=constants.AWS_S3_ENDPOINT,
)

bucket = constants.AWS_S3_BUCKET
alt_bucket = constants.AWS_S3_BUCKET_ALT


# Create a bucket policy
bucket_name = bucket

bucket_policy = {
  'Version': '2012-10-17',
  'Id': 'S3PolicyIdNew2',
  'Statement': [{
      'Action': [
        's3:ListBucket',
        's3:PutObject'
      ],
      'Resource': [
        'arn:aws:s3:::{bucket}',
        'arn:aws:s3:::{bucket}/*'
      ],
      'Effect': 'Allow',
      'Principal': '{alt_bucket}',
      'Sid': 'Granting 2nd userID permission to {bucket} bucket '
    },
    {
      'Action': [
        's3:DeleteObject',
        's3:DeleteObjectVersion'
      ],
      'Resource': [
        'arn:aws:s3:::{bucket}/*'
      ],
      'Effect': 'Deny',
      'Principal': '{alt_bucket}',
      'Sid': 'Denying 2nd userID Overwrite and Delete permissions to {bucket} bucket '
    }]
}

# Convert the policy from JSON dict to string
bucket_policy = json.dumps(bucket_policy)

# Set the new policy
s3_client.put_bucket_policy(Bucket=bucket, Policy=bucket_policy)

########################################################
# Retrieve the policy of the specified bucket
result = s3_client.get_bucket_policy(Bucket=bucket)
print(result['Policy'])

########################################################
# Delete a bucket's policy
s3_client.delete_bucket_policy(Bucket=bucket)