# -------------------------------------------------------------------------------
# Name:        set_s3_bucket_cors.py
# Purpose:     This script gets or sets a CORS setting for an object storage bucket
#
# Author:      Peter Platten
#
# Created:     2024
# Copyright:   (c) Peter Platten & Optimization Team 2024
# Licence:     mine
#
# Notes:       see https://docs.aws.amazon.com/AmazonS3/latest/userguide/ManageCorsUsing.html
#
# -------------------------------------------------------------------------------


import logging
import boto3
from botocore.exceptions import ClientError

endpoint = "https://nrs.objectstore.gov.bc.ca:443"
access_key = "nr-myaccesskey-pr"
secret_key = "123456789"
bucket_name = "bucketname"

# AllowedOrigins should not use a wildcard
cors_configuration = {
    'CORSRules': [{
        'AllowedHeaders': ['*'],
        'AllowedMethods': ['HEAD', 'GET', 'PUT', 'POST', 'DELETE'],
        'AllowedOrigins': ['https://apps.silver.devops.gov.bc.ca'],
        'ExposeHeaders': ['ETag', 'x-amz-request-id','Access-Control-Allow-Origin'],
        'MaxAgeSeconds': 3000
    }]
}


# Retrieve the CORS configuration
def get_bucket_cors(s3_client, bucket_name):
    print("Checking CORS Rules:")
    try:
        response = s3_client.get_bucket_cors(Bucket=bucket_name)
        print(response['CORSRules'])
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchCORSConfiguration':
            print(f"No CORS Rules are currently set on {bucket_name}.")
        else:
            # AllAccessDisabled error == bucket not found
            logging.error(e)
        
    print("")


# Set a CORS configuration
def set_bucket_cors(s3_client, bucket_name, cors_configuration):

    try:
        s3_client.put_bucket_cors(Bucket=bucket_name, CORSConfiguration=cors_configuration)    
    except ClientError as e:        
        logging.error(e)
    # Set the CORS configuration
    print("Set CORS Complete")
    print("")


try:

    # Get the service client with sigv4 configured    
    s3_client = boto3.client('s3',
        endpoint_url=endpoint,        
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key)

    # Check pre-existing CORS Rules by printing to console
    get_bucket_cors(s3_client, bucket_name)
    
    # Set the new rules
    set_bucket_cors(s3_client, bucket_name, cors_configuration)

    # Check that the new rules applied successfully
    get_bucket_cors(s3_client, bucket_name)


except ClientError as e:
    logging.error(e)

