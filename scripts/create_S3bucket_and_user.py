# -------------------------------------------------------------------------------
# Name:        create_S3bucket_and_user.py
# Purpose:     login into the S3 DELL management and create buckets and users in a standardize way.
#
# Author:      MRDOUVIL
#
# Created:     16-12-2019
# Copyright:   (c) MRDOUVIL 2019
# Licence:     <your licence>
# dependent on https://github.com/EMCECS/python-ecsclient
# TODO: build envioment with requirements list needs to be deployed before running
# TODO: parameters and encrypted password settings need to be in runtime env properly
# -------------------------------------------------------------------------------

import random
import string
import argparse

from ecsclient.client import Client
import getpass
import sys


def parse_args():
    print("Number of arguments:", len(sys.argv), "arguments.")
    print("Argument List:", str(sys.argv))

    syntaxcmd = 'create_s3bucket_and_user.py <command - createuser, createbucket, listuser, listbuckets, listbucketsizes> '
    syntaxcmd = syntaxcmd + '-u <DELLNamespace_adminuser> -p <DellNamespace_adminpassword> -n <namespace - default is "nrs">'

    if len(sys.argv) < 2:
        print(syntaxcmd)
        sys.exit(2)

    parser = argparse.ArgumentParser(description="command line client")
    parser.set_defaults(funct=argparser_handler)

    parser.add_argument(
        "-u",
        dest="user",
        help="user.  If this argument is not passed it will be requested.",
        metavar="user",
        type=str,
    )
    parser.add_argument(
        "-p",
        dest="password",
        help="password.  If this argument is not passed it will be requested.",
        metavar="password",
        type=str,
    )
    parser.add_argument(
        "-",
        "--command",
        dest="command",
        required=True,
        help="specify the action/command to run - createuser, createbuckets, listuser, listbuckets, listbucketsizes",
        metavar="command",
        type=str,
    )
    parser.add_argument(
        "-r",
        "--replicationgroup",
        dest="replicationgroup",
        default="urn:storageos:ReplicationGroupInfo:4759217e-b060-4abb-a100-6a50686d6cf8:global",
        required=False,
        help="replication group with the DELL APplicance (default is 'urn:storageos:ReplicationGroupInfo:4759217e-b060-4abb-a100-6a50686d6cf8:global'",
        metavar="replication group",
        type=str,
    )
    parser.add_argument(
        "-ou",
        "--objectuser",
        dest="objectuser",
        required=False,
        help="Object User to Create if function is set to 'createUser'",
        metavar="objectuser",
        type=str,
    )
    parser.add_argument(
        "-n",
        "--namespace",
        dest="namespace",
        default="nrs",
        required=False,
        help="namespace to access in object storage (default is 'nrs')",
        metavar="namespace",
        type=str,
    )

    parser.add_argument("--encrypt", dest="encryption_enabled", action="store_true")
    parser.add_argument("--no-encrypt", dest="encryption_enabled", action="store_false")
    parser.set_defaults(encryption_enabled=False)

    parser.add_argument(
        "-e",
        "--endpoint",
        dest="endpoint",
        default="https://mgmt.objectstore.gov.bc.ca:4443",
        required=False,
        help="REST Endpoint to access DELL management API (default is 'https://mgmt.objectstore.gov.bc.ca:4443')",
        metavar="rest admin Endpoint",
        type=str,
    )

    args = parser.parse_args()
    args.funct(args)


def argparser_handler(args):
    command = args.command
    print("The command to run is: ", command)
    replicationgroup = args.replicationgroup
    print("The replication group is: ", replicationgroup)
    user = args.user
    password = args.password
    print("The admin user is: ", user)
    objectuser = args.objectuser
    print("The object user is: ", object)
    namespace = args.namespace
    print("The namespace is: ", namespace)
    endpoint = args.endpoint
    print("The endpoint is: ", endpoint)
    encryption_enabled = args.encryption_enabled

    if args.command == "createuser":
        login(user, password)
        # login to the DELL management console
        client = adminLogin(user, password, endpoint)
        createUser(objectuser, namespace, client)
    if args.command == "createbucket":
        login(user, password)
        # login to the DELL management console
        client = adminLogin(user, password, endpoint)
        createBucket(encryption_enabled, replicationgroup, namespace, client)
    if args.command == "listbuckets":
        login(user, password)
        # login to the DELL management console
        client = adminLogin(user, password, endpoint)
        listBuckets(namespace, client)
    if args.command == "listbucketsizes":
        login(user, password)
        # login to the DELL management console
        client = adminLogin(user, password, endpoint)
        listBucketSizes(namespace, client)
    if args.command == "listusers":
        login(user, password)
        # login to the DELL management console
        client = adminLogin(user, password, endpoint)
        listUsers(namespace, client)


# prompt if user and password is not given in the command line
def login(user, password):
    if not user:
        user = input("User:")
    if not password:
        password = getpass.getpass()
    print("user:", user)
    print("password:", password)


# login to the administrative DELL ECS API
def adminLogin(user, password, endpoint):
    client = Client(
        "3",
        username=user,
        password=password,
        token_endpoint=endpoint + "/login",
        cache_token=False,
        ecs_endpoint=endpoint,
    )

    print("----------LOGGED IN ADMIN USER IS:")
    print(client.user_info.whoami())
    print()
    return client


# generate a random string used for bucket naming
def randomString(stringLength=10):
    """Generate a random string of fixed length"""
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(stringLength))


# create a user in the Dell appliance based on command line inputs
def createUser(objectuser, namespace, client):
    print("Creating DELL ECS User account")
    client.object_user.create(objectuser, namespace)
    print('created user "' + objectuser + '"in namepace - ' + namespace)


# create a bucket in the Dell appliance based on command line inputs
def createBucket(encryption_enabled, replicationgroup, namespace, client):
    print("Creating DELL ECS Bucket")
    # bucket_name, replicationgroup='', filesystem_enabled=False, head_type=None, namespace=None, stale_allowed=False,  metadata=None, encryption_enabled=False):
    metadata = [
        {"datatype": "datetime", "name": "CreateTime", "type": "System"},
        {"datatype": "datetime", "name": "LastModified", "type": "System"},
        {"datatype": "string", "name": "ObjectName", "type": "System"},
        {"datatype": "string", "name": "Owner", "type": "System"},
        {"datatype": "integer", "name": "Size", "type": "System"},
    ]
    # print(metadata)

    bucketname = randombucketname()
    print("creating bucket:  " + bucketname)
    client.bucket.create(
        bucketname,
        replicationgroup,
        False,
        None,
        namespace,
        False,
        metadata,
        encryption_enabled,
    )


# list the buckets in the Dell appliance based on command line inputs
def listBuckets(namespace, client):
    print("List of buckets within the " + namespace + " namespace:")

    bucket = client.bucket.list(namespace)
    print(bucket)


# list the buckets in the Dell appliance based on command line inputs, but make extra requests to get size data for each bucket
def listBucketSizes(namespace, client):
    print(
        "List of buckets within the " + namespace + " namespace, including bucket size:"
    )

    # Get a list of bucket names. Don't stop at the default of 100 buckets (nrs is at 73 on 2021-05-27)
    namespaceresponse = client.bucket.list(namespace, limit=1000)
    bucketlist = namespaceresponse["object_bucket"]
    for bucket in bucketlist:
        bucketresponse = client.bucket.getbucketdetails(namespace, bucket["name"])
        print(bucketresponse)


# list the users in the Dell appliance based on command line inputs
def listUsers(namespace, client):
    userslist = client.object_user.list()
    users = userslist["blobuser"]
    print("List of Object users with the " + namespace + " namespace:")
    for user in users:
        print(user)


# generate a random bucket name based on length given - standard/default is six
def randombucketname():
    randomname = randomString(6)
    # print ("Random String is ", randomname)
    return randomname


def main():
    pass


if __name__ == "__main__":
    parse_args()
    main()
