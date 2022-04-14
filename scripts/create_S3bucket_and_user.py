# -------------------------------------------------------------------------------
# Name:        create_S3bucket_and_user.py
# Purpose:     login into the S3 DELL management and create buckets using a config file.
#
# Author:      PPLATTEN, HHAY, updated from MDOUVILLE's script
#
# Created:     April-2022
#
# dependent on https://github.com/EMCECS/python-ecsclient
# TODO: build envioment with requirements list needs to be deployed before running
# TODO: parameters and encrypted password settings need to be in runtime env properly
# -------------------------------------------------------------------------------

import random
import string

import constants

import time
from ecsclient.common.exceptions import ECSClientException
from ecsclient.client import Client as ESCCLlient


# login to the administrative DELL ECS API
def adminLogin():

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
        client = adminLogin()
    except ECSClientException:
        counter = 3
        while counter > 0:
            print("Connection to S3 Failed, trying again in 10")
            time.sleep(10)
            try:
                client = adminLogin()
                counter = 0
            except ECSClientException:
                if counter == 1:
                    print("Connection to S3 Failed, closing")
                pass
            counter = counter - 1
    return client


# generate a random string used for bucket naming
def randomString(stringLength=10):
    """Generate a random string of fixed length"""
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(stringLength))


# create a user in the Dell appliance based on command line inputs
def createUser(objectuser, client):
    print("Creating DELL ECS User account")
    client.object_user.create(objectuser, constants.OBJSTOR_MGMT_NAMESPACE)
    print(f"Created user {objectuser}")


# create a bucket in the Dell appliance based on command line inputs
def createBucket(bucket_config, client):
    print("Creating DELL ECS Bucket")
    metadata = [
        {"datatype": "datetime", "name": "CreateTime", "type": "System"},
        {"datatype": "datetime", "name": "LastModified", "type": "System"},
        {"datatype": "string", "name": "ObjectName", "type": "System"},
        {"datatype": "string", "name": "Owner", "type": "System"},
        {"datatype": "integer", "name": "Size", "type": "System"},
    ]

    bucketname = bucket_config["bucketname"]

    result = client.bucket.create(
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
    client.bucket.set_owner(bucketname,bucket_config["owner"])
    # client.bucket.set_quota()
    # client.bucket.set_metadata()
    # client.bucket.set_retention()?

    print(f"Created bucket: {bucketname}")
    client.bucket.delete(bucketname)
    # Still to handle:
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


# list the buckets in the Dell appliance based on command line inputs
def bucketExists(bucketname, client):

    buckets = client.bucket.list(constants.OBJSTOR_MGMT_NAMESPACE)
    for bucket in buckets["object_bucket"]:
        if bucket["name"] == bucketname:
            return True
    return False


# list the users in the Dell appliance based on command line inputs
def userExists(username, client):
    userslist = client.object_user.list()
    users = userslist["blobuser"]
    for user in users:
        if user["userid"] == username:
            return True
    return False


# generate a random bucket name based on length given - standard/default is six
def randombucketname():
    randomname = randomString(6)
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
    buckets = [
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

    client = adminLogin()

    for bucket in buckets:
        owner = bucket["owner"]
        if userExists(owner, client):
            print("Owner already exists")
        else:
            createUser(owner, client)
            print(f"Created {owner}")
        bucketname = bucket["bucketname"]
        if bucketExists(bucketname, client):
            print("Bucket already exists")
        else:
            createBucket(bucket, client)
            print(f"Created {bucketname}")


if __name__ == "__main__":
    main()
