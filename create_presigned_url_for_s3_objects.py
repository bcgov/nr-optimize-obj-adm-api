# -------------------------------------------------------------------------------
# Name:        create_presigned_url_for_s3_objects.py
# Purpose:     This script returns an URL that provides access to an S3 object for a
#              pre-determined amount of time (expiration)
#              1.) looks for env vars for OBJSTOR_PUBLIC_ENDPOINT, AWS_ACCESS_KEY_ID
#                  and AWS_SECRET_ACCESS_KEY
#              2.) looks for the expiration/bucket name as parameters with a default
#              3.) looks for the object as a command line config
#
# Author:      Michelle Douville
#              edits by the Optimization Team
#
# Created:     2021
# Copyright:   (c) Michelle Douville & IITD Optimization Team 2021
# Licence:     mine
#
# Notes:       see https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-presigned-urls.html
#
# usage: create_presigned_url_for_s3_objects.py -o <object> -t <time>
# example:  create_presigned_url_for_s3_objects.py -o test.txt -t 3600
# -------------------------------------------------------------------------------


import logging
import argparse
import sys
import constants
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

# Get the service client with sigv4 configured
s3 = boto3.client("s3", config=Config(signature_version="s3v4"))

object2share = ""  # name of object to share
expiration = ""  # URL expiration time in seconds
syntaxcmd = "Insufficient number of commands passed: create_presigned_url_for_s3_objects.py -o <object> -t <time>"

if len(sys.argv) < 2:
    print(syntaxcmd)
    sys.exit(2)

parser = argparse.ArgumentParser()

parser.add_argument(
    "-o",
    "--object",
    dest="object2share",
    required=True,
    help="object aka file name",
    metavar="string",
    type=str,
)
parser.add_argument(
    "-t",
    "--time",
    dest="expiration",
    required=True,
    help="expiration time in seconds",
    metavar="string",
    type=str,
)
args = parser.parse_args()

object2share = args.object2share
expiration = args.expiration

# provide the default parameters for bucketname for the S3 Object
bucketname = "nrs-iit"

# this script requires access to secret/secure information store as environment variables that are picked up at runtime
AWS_SERVER_PUBLIC_KEY = (
    constants.AWS_SERVER_PUBLIC_KEY
)  # access key for s3 object storage
AWS_SERVER_SECRET_KEY = (
    constants.AWS_SERVER_SECRET_KEY
)  # secret ky for S3 object storage
OBJSTOR_PUBLIC_ENDPOINT = (
    constants.OBJSTOR_PUBLIC_ENDPOINT
)  # endpoint for S3 Object Storage -- if this isn't specified it will try and go to Amazon S3


# use third party object storage
s3 = boto3.resource(
    "s3",
    endpoint_url=OBJSTOR_PUBLIC_ENDPOINT,
    aws_access_key_id=AWS_SERVER_PUBLIC_KEY,
    aws_secret_access_key=AWS_SERVER_SECRET_KEY,
)

# define the function for creating the URL, the script if it works will return a shareable URL in the print output
def create_presigned_url(
    endpoint_url,
    bucket_name,
    object_name,
    expiration=expiration,
):

    # Generate a presigned URL for the S3 object
    s3_client = boto3.client(
        "s3",
        endpoint_url=OBJSTOR_PUBLIC_ENDPOINT,
        aws_access_key_id=AWS_SERVER_PUBLIC_KEY,
        aws_secret_access_key=AWS_SERVER_SECRET_KEY,
    )

    try:
        response = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": object_name},
            ExpiresIn=expiration,
        )
        print(response)

    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL
    return response


# run the function with the give parameters.
create_presigned_url(OBJSTOR_PUBLIC_ENDPOINT, bucketname, object2share)
