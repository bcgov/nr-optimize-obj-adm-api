# -------------------------------------------------------------------------------
# Name:        create_S3bucket_and_user.py
# Purpose:     login into the S3 DELL management and create buckets using a config file.
#
# Author:      PPLATTEN, HHAY
#
# Created:     April-2022
#
# WORK IN PROGRESS - SCRIPT DOES NOT WORK YET
# -------------------------------------------------------------------------------

import random
import string

import constants

import time
from ecsclient.common.exceptions import ECSClientException
from ecsclient.client import Client as ESCCLlient

from minio import Minio
from minio.error import S3Error

from boto3 import client as boto_client


# login to the administrative DELL ECS API
def admin_login():

    client = ESCCLlient(
        "3",
        username=constants.OBJSTOR_ADMIN,
        password=constants.OBJSTOR_ADMIN_PASS,
        token_endpoint=constants.OBJSTOR_MGMT_ENDPOINT + "/login",
        cache_token=False,
        ecs_endpoint=constants.OBJSTOR_MGMT_ENDPOINT,
    )
    print("----------LOGGED IN ADMIN USER IS:")
    print(client.user_info.whoami())
    print()
    return client


def try_admin_login():
    client = None
    try:
        client = admin_login()
    except ECSClientException:
        counter = 3
        while counter > 0:
            print("Connection to S3 Failed, trying again in 10")
            time.sleep(10)
            try:
                client = admin_login()
                counter = 0
            except ECSClientException:
                if counter == 1:
                    print("Connection to S3 Failed, closing")
                pass
            counter = counter - 1
    return client


# generate a random string used for bucket naming
def random_string(stringLength=10):
    """Generate a random string of fixed length"""
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(stringLength))


# create a user in the Dell appliance based on command line inputs
def ecs_create_user(objectuser, client):
    print("Creating DELL ECS User account")
    client.object_user.create(objectuser, constants.OBJSTOR_MGMT_NAMESPACE)
    print(f"Created user {objectuser}")


# create a bucket in the Dell appliance based on command line inputs
def ecs_create_bucket(bucket_config, client):
    print("Creating DELL ECS Bucket")
    metadata = [
        {"datatype": "datetime", "name": "CreateTime", "type": "System"},
        {"datatype": "datetime", "name": "LastModified", "type": "System"},
        {"datatype": "string", "name": "ObjectName", "type": "System"},
        {"datatype": "string", "name": "Owner", "type": "System"},
        {"datatype": "integer", "name": "Size", "type": "System"},
    ]

    bucketname = bucket_config["bucketname"]

    client.bucket.create(
        bucketname,
        client.replication_group.list()["data_service_vpool"][0]["id"],
        bucket_config["filesystem_enabled"],
        bucket_config["head_type"],
        constants.OBJSTOR_MGMT_NAMESPACE,
        bucket_config["stale_enabled"],
        metadata,
        bucket_config["encryption_enabled"]
    )
    bucket = client.bucket.get(bucketname)
    # Invalid permissions error for set owner
    # client.bucket.set_owner(constants.OBJSTOR_MGMT_NAMESPACE, bucketname, bucket_config["owner"])
    # client.bucket.set_quota()
    # client.bucket.set_metadata()
    # client.bucket.set_retention()?

    print(f"Created bucket: {bucketname}")

    # Does not handle these attributes:
    # bucket = {
    #     "owner": "nr-skeena-prd",
    #     "notification-quota": 50,
    #     "block-quota": 75,
    #     "tags": {
    #       "Project": "Skeena Large File Service #7100000",
    #       "Branch": "Natural Resource Information & Digital Services",
    #       "Ministry": "LWRS",
    #       "Data Custodian": "Andy Muma",
    #       "Data Steward": "Andy Muma"
    #     }
    # }


# list the users in the Dell appliance based on command line inputs
def ecs_user_exists(username, client):
    userslist = client.object_user.list()
    users = userslist["blobuser"]
    for user in users:
        if user["userid"] == username:
            return True
    return False


# generate a random bucket name based on length given - standard/default is six
def random_bucket_name():
    randomname = random_string(6)
    # print ("Random String is ", randomname)
    return randomname


def main():

    # What the values mean:
    # filesystem_enabled allows the bucket to be used as a Hadoop HDFS or NFS file system, usually False for us.
    # head_type is.. False?
    # encryption_enabled means that the data will be encrypted at rest in the datacenter
    # stale_enabled means that if the primary datacenter is inaccessible users will be redirected to the backup datacenter
    # notification-quota notifies OCIO when data consumption exceeds this amount of GB; we haven't ever heard something back from this
    # block-quota is a cutoff in GB; data consumption cannot be uploaded over this value
    buckets_cfg = [
        {
            "bucketname": "peter-bucket-1",
            "owner": "nr-skeena-prd",
            "filesystem_enabled": False,
            "head_type": None,
            "encryption_enabled": False,
            "stale_enabled": True,
            "notification-quota": 50,
            "block-quota": 75,
            "tags": {
                "Project": "Skeena Large File Service #7100000",
                "Branch": "Natural Resource Information & Digital Services",
                "Ministry": "LWRS",
                "Data Custodian": "Andy Muma",
                "Data Steward": "Andy Muma"
            }
        }
    ]
    s3 = boto_client(
        "s3",
        endpoint_url=constants.OBJSTOR_MGMT_ENDPOINT,
        aws_access_key_id=constants.OBJSTOR_ACCESS_KEY,
        aws_secret_access_key=constants.OBJSTOR_SECRET_KEY,
    )
    bucket_name = "peter-bucket-1"
    # buckets = s3.put(Bucket=bucket_name, ExpectedBucketOwner=constants.OBJSTOR_ADMIN)
    response = s3.put_bucket_tagging(
        Bucket=bucket_name,
        Tagging={
            'TagSet': [
                {
                    'Key': 'tag1',
                    'Value': 'val1'
                },
            ]
        },
        ExpectedBucketOwner=constants.OBJSTOR_ADMIN
    )

    # Create users with ECS Client, because minio client can't
    ecs_client = try_admin_login()
    for bucket in buckets_cfg:
        owner = bucket["owner"]
        if ecs_user_exists(owner, ecs_client):
            print("Owner already exists")
        else:
            ecs_create_user(owner, ecs_client)
            print(f"Created {owner}")

    # Create buckets also uses minio_client for some operations not available in ECS Client
    minio_client = Minio(
        endpoint=constants.OBJSTOR_ENDPOINT,
        access_key=constants.OBJSTOR_ACCESS_KEY,
        secret_key=constants.OBJSTOR_SECRET_KEY,
        region="US",
    )

    for bucket_cfg in buckets_cfg:
        bucket_name = bucket_cfg["bucketname"]
        if minio_client.bucket_exists(bucket_name):
            print("(minio) Bucket already exists")
        else:
            ecs_create_bucket(bucket_cfg, ecs_client)
            print(f"Created {bucket_name}")

            # ecs_create_bucket does not handle these attributes:
            # bucket = {
            #     "owner": "nr-skeena-prd",
            #     "notification-quota": 50,
            #     "block-quota": 75,
            #     "tags": {
            #       "Project": "Skeena Large File Service #7100000",
            #       "Branch": "Natural Resource Information & Digital Services",
            #       "Ministry": "LWRS",
            #       "Data Custodian": "Andy Muma",
            #       "Data Steward": "Andy Muma"
            #     }
            # }
            # Try using minio!

        for bucket in buckets:
            print(bucket.name)
        tags = {}
        for tag in bucket_cfg["tags"]:
            tags[tag] = bucket_cfg["tags"][tag]
        minio_client.set_bucket_tags(bucket_name, tags)
        print(f"Created {bucket_name} with minio")


if __name__ == "__main__":
    main()
