# -------------------------------------------------------------------------------
# Name:        relay_bucket_data.py
# Purpose:     login into the S3 DELL management, check all bucket sizes, push bucket sizes to openshift database.
#
# Author:      IITD Optimize Team, (PPLATTEN)
#
# Created:     2021-08-20
#
# Example run: relay_bucket_data.py -objstor_admin <objstor_admin> -objstor_pass <objstor_pass> -postgres_user <postgres_user> -postgres_pass <postgres_pass>
# Note: Parameters will override environment variables.
#
# TODO: Verify bucket data is being imported correctly
# TODO: Run from Internal Server which has a connection to openshift database
# TODO: Push data to database instead of CSV?
# -------------------------------------------------------------------------------

from datetime import datetime

import constants
import time
import argparse

from ecsclient.common.exceptions import ECSClientException
from ecsclient.client import Client


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


def try_admin_login(user, password, endpoint):
    client = None
    try:
        client = adminLogin(user, password, endpoint)
    except ECSClientException:
        counter = 3
        while counter > 0:
            print("Connection to S3 Failed, trying again in 10")
            time.sleep(10)
            try:
                client = adminLogin(constants.OBJSTOR_ADMIN, constants.OBJSTOR_ADMIN_PASS, constants.OBJSTOR_MGMT_ENDPOINT)
                counter = 0
            except ECSClientException:
                if counter == 1:
                    print("Connection to S3 Failed, closing")
                pass
            counter = counter - 1
    return client


# list the buckets in the Dell appliance based on command line inputs, but make extra requests to get size data for each bucket
def get_buckets(namespace, client):
    print(
        "Getting a list of buckets within the " + namespace + " namespace:"
    )

    # Get a list of bucket names. Don't stop at the default of 100 buckets (nrs is at 73 on 2021-05-27)
    namespace_response = client.bucket.list(namespace, limit=10000)
    bucket_list = namespace_response["object_bucket"]
    bucket_dict = {}
    for bucket in bucket_list:
        bucket_response = client.bucket.getbucketdetails(namespace, bucket["name"])
        bucket_response["owner"] = bucket["owner"]
        bucket_response["softquota"] = bucket["softquota"]
        bucket_response["notification_size"] = bucket["notification_size"]
        bucket_response["created"] = datetime.strptime(bucket['created'].split('T')[0], '%Y-%m-%d')
        if "owner" not in bucket:
            bucket_response["owner"] = "No Owner"
        bucket_response["project"] = "No Project"
        bucket_response["organization"] = "No Organization"
        bucket_response["custodian"] = "No Custodian"
        bucket_response["steward"] = "No Steward"
        if "TagSet" in bucket_response:
            for tag in bucket["TagSet"]:
                if tag["Key"] == "Project":
                    bucket_response["project"] = tag["Value"]
                elif tag["Key"] == "Organization":
                    bucket_response["organization"] = tag["Value"]
                elif tag["Key"] == "Data Custodian":
                    bucket_response["custodian"] = tag["Value"]
                elif tag["Key"] == "Data Steward":
                    bucket_response["steward"] = tag["Value"]
        bucket_dict[bucket_response["name"]] = bucket_response
    return bucket_dict


def get_arg_parser():
    parser = argparse.ArgumentParser()
    # relay_bucket_data.py -objstor_admin <objstor_admin> -objstor_pass <objstor_pass> -postgres_user <postgres_user> -postgres_pass <postgres_pass>"
    parser.add_argument(
        "-objstor_admin",
        "--objstor_admin",
        dest="objstor_admin",
        required=False,
        help="admin account for accessing object storage management api",
        metavar="string",
        type=str
    )
    return parser.parse_args()


def main(argv):

    args = get_arg_parser()

    objstor_admin = constants.OBJSTOR_ADMIN if args.objstor_admin is None else args.objstor_admin
    print(f"objstor_admin:{objstor_admin}")
