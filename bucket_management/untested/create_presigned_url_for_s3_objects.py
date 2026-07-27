# -------------------------------------------------------------------------------
# Name:        create_presigned_url_for_s3_objects.py
# Purpose:     This script returns an URL that provides access to an S3 object for a
#              pre-determined amount of time (expiration)
#              1.) looks for env vars for OBJSTOR_PUBLIC_ENDPOINT, ACCESS_KEY
#                  and SECRET_KEY
#              2.) looks for the bucket name as a parameter with a default
#              3.) looks for the object and expiration time as a command line config
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


### How to use a Python script to perform URL Sharing from Object Storage

# This will output a pre-signed URL for your object that will allow the user to download it for a pre-determined length of time.

# 1. Create an .env file that contains the following information:
#     - *OBJSTOR_PUBLIC_ENDPOINT = 'https://nrs.objectstore.gov.bc.ca:443'*
#     - *AWS_ACCESS_KEY = 'YOUR_OBJECT_STORAGE_USER_ID'*
#     - *AWS_SERVER_SECRET_KEY = 'YOUR_OBJECT_STORAGE_SECRET_KEY'*
# 3. Download **requirements.txt, constants.py** and **create_presigned_url_for_s3_objects.py** from this Object Storage GitHub repo
# 4. Save all 4 files in the same folder
# 5. Open your code editor of choice (our team uses Visual Studio Code) and point your directory to the folder with those files
# 6. Open a cmd terminal and run *pip install -r requirements.txt* to install the python packages needed to run scripts from our GitHub repo.
# 7. Open **create_presigned_url_for_s3_objects.py** and change the variable for bucketname to your bucket name. Save your changes.
# 8. Next, run *python create_presigned_url_for_s3_objects.py -o \<object> -t \<time>*
#     - **Example:** create_presigned_url_for_s3_objects.py -o test.txt -t 3600

# **SECURITY CONSIDERATIONS**
  
# What are requestors of your pre-signed URLs allowed access to – everything, or are some areas restricted? In the case of restrictions, the Object Storage User ID used in the .env file should have a bucket policy applied that grants access only to what a requestor would be allowed to download from your bucket. [Our team](mailto:nrids.optimize@gov.bc.ca) can set this up by request through the Object Storage Admin Dashboard.\
# The command-line variable value for “expiration” is counted in seconds. It is strongly recommended that you keep the expiration times short to ensure users can use only the current signed URLs and not ones signed in the past.
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
AWS_ACCESS_KEY = (
    constants.AWS_ACCESS_KEY
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
    aws_access_key_id=AWS_ACCESS_KEY,
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
    boto_client = boto3.client(
        "s3",
        endpoint_url=OBJSTOR_PUBLIC_ENDPOINT,
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SERVER_SECRET_KEY,
    )

    try:
        response = boto_client.generate_presigned_url(
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
