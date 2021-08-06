"""example of using the BOTO3 python client libraries for generating a token based expiry URL to access objects in S3 Storage buckets
   Data: 2021-05-03
   Author: michelle.douville@gov.bc.ca
   usage: python create_presigned_url_for_s3_objects.py
   NOTES:  (currently there are no command line configs, but looks for env vars for OBJSTOR_PUBLIC_ENDPOINT, AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY,
   and the expiration/bucket name as parameters with a default)
   This script returns an URL that provides access to a S3 object for a pre-determined amount of time (expiration)
 """

# see https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-presigned-urls.html

import logging
import constants
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

# Get the service client with sigv4 configured
s3 = boto3.client("s3", config=Config(signature_version="s3v4"))

object2share = "test.txt"  # name of object to share

# provide the default parameters for expiry, endpoint, and bucketname for the S3 Object
expiration = 3600  # default is 1 hour
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
