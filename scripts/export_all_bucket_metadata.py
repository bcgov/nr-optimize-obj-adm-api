# -------------------------------------------------------------------------------
# Name:        export_all_bucket_metadata.py
# Purpose:     login into the S3 DELL management, export all bucket sizes and tags to excel.
#
# Author:      IITD Optimize Team, (PPLATTEN)
#
# Created:     2022-05-11
#
# Example run: export_all_bucket_metadata.py -objstor_admin <objstor_admin> -objstor_pass <objstor_pass>
# Note: Parameters will override environment variables.
#
# -------------------------------------------------------------------------------

import datetime

import argparse
import constants
import pandas as pd
import sys
import time

from ecsclient.common.exceptions import ECSClientException
from ecsclient.client import Client


# login to the administrative DELL ECS API
def admin_login(user, password, endpoint):
    client = Client(
        "3",
        username=user,
        password=password,
        token_endpoint=endpoint + "/login",
        cache_token=False,
        ecs_endpoint=endpoint,
        request_timeout=45.0
    )

    print("----------LOGGED IN ADMIN USER IS:")
    print(client.user_info.whoami())
    print()
    return client


def try_admin_login(user, password, endpoint):
    client = None
    counter = 4
    while counter > 0:
        try:
            client = admin_login(constants.OBJSTOR_ADMIN, constants.OBJSTOR_ADMIN_PASS, constants.OBJSTOR_MGMT_ENDPOINT)
            counter = 0
        except ECSClientException as ecsclient_ex:
            if ecsclient_ex.message == 'Invalid username or password':
                message_detail = "The Export All Bucket MetaData script failed to sign in to Object Storage Management " \
                    + "API due to an invalid username or password error.<br />" \
                    + "<br />Username: " + constants.OBJSTOR_ADMIN \
                    + "<br />Message Detail: " + ecsclient_ex.message
                print(message_detail)
                counter = 0
                pass
            elif counter == 1:
                print("Connection to S3 Failed, closing")
                message_detail = "The Export All Bucket MetaData script failed to sign in to Object Storage Management " \
                    + "API with the following message.<br />" \
                    + "<br />Message: " + ecsclient_ex.message \
                    + "<br />Message Detail: " + ecsclient_ex.message_detail \
                    + "<br />Username: " + constants.OBJSTOR_ADMIN
                print(message_detail)
            else:
                print("Connection to S3 Failed, trying again in 10")
                time.sleep(10)
            pass
        counter = counter - 1
    return client


# Print out bucket details and tags for convenience.
def print_bucket_tags(buckets):
    print(
        "stashing a list of bucket tags"
    )

    all_tags = []
    for bucket_name in buckets:
        bucket = buckets[bucket_name]
        tags_dict = {}
        for tag_kvp in bucket["TagSet"]:
            tags_dict[tag_kvp["Key"]] = tag_kvp["Value"]
        for tag_key in tags_dict:
            if tag_key not in all_tags:
                all_tags.append(tag_key)
        bucket["TagsDict"] = tags_dict

    row = []
    rows = []

    # build headers
    row.append("Bucket Name")
    row.append("Bucket Username")
    row.append("Created Date")
    row.append("Total GB")
    row.append("Object Count")
    for tag in all_tags:
        row.append(tag)
    rows.append(row)

    # build rows
    for bucket_name in buckets:
        bucket = buckets[bucket_name]
        row = []
        row.append(bucket_name)
        row.append(bucket["owner"])
        row.append(bucket["created"].strftime('%Y-%m-%d'))
        row.append(bucket["total_size"])
        row.append(str(bucket["total_objects"]))
        tags_dict = bucket["TagsDict"]
        for tag in all_tags:
            if tag in tags_dict:
                row.append(tags_dict[tag])
            else:
                row.append("None")
        rows.append(row)

    for row in rows:
        print(",".join(row))


# Save bucket details as csv file
def save_bucket_details(buckets):
    # clean up data
    for bucket_name in buckets:
        bucket = buckets[bucket_name]
        del bucket["vpool_id"]
        bucket["total_size_gb"] = bucket["total_size"]
        del bucket["total_size"]
        del bucket["total_size_unit"]
        del bucket["sample_time"]
        del bucket["sample_date"]
        del bucket["month"]

    current_time = datetime.date.today().isoformat()
    df = pd.DataFrame(buckets).T
    df.to_excel(f'bucket-tags-{current_time}.xlsx')


# list the buckets in the Dell appliance based on command line inputs, but make extra requests to get size data for each bucket
def get_buckets(namespace, client):
    print(
        "Getting a list of buckets within the " + namespace + " namespace:"
    )

    # Get a list of bucket names. Don't stop at the default of 100 buckets (nrs is at 73 on 2021-05-27)
    namespace_response = client.bucket.list(namespace, limit=10000)
    bucket_list = namespace_response["object_bucket"]
    bucket_dict = {}
    sample_date = datetime.date.today()
    sample_month = datetime.datetime.today().strftime('%Y-%m')
    for bucket in bucket_list:
        bucket_response = client.bucket.getbucketdetails(namespace, bucket["name"])
        bucket_response["owner"] = bucket["owner"]
        bucket_response["softquota"] = bucket["softquota"]
        bucket_response["notification_size"] = bucket["notification_size"]
        bucket_response["created"] = datetime.datetime.strptime(bucket['created'].split('T')[0], '%Y-%m-%d')
        bucket_response["month"] = sample_month
        bucket_response["sample_date"] = sample_date
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
                elif tag["Key"] == "Ministry":
                    bucket_response["ministry"] = tag["Value"]
        bucket_dict[bucket_response["name"]] = bucket_response
    return bucket_dict


# if command line arguments were provided, override constants.py provided environment variables
def handle_input_arguments():
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
    parser.add_argument(
        "-objstor_pass",
        "--objstor_pass",
        dest="objstor_pass",
        required=False,
        help="admin password for accessing object storage management api",
        metavar="string",
        type=str
    )

    args = parser.parse_args()

    # Override constants
    if args.objstor_admin is not None:
        constants.OBJSTOR_ADMIN = args.objstor_admin
    if args.objstor_pass is not None:
        constants.OBJSTOR_ADMIN_PASS = args.objstor_pass


def print_constants():
    print("OBJSTOR_ADMIN: " + constants.OBJSTOR_ADMIN)
    print("OBJSTOR_ADMIN_PASS: " + constants.OBJSTOR_ADMIN_PASS)
    print("OBJSTOR_MGMT_ENDPOINT: " + constants.OBJSTOR_MGMT_ENDPOINT)
    print("OBJSTOR_MGMT_NAMESPACE: " + constants.OBJSTOR_MGMT_NAMESPACE)


def main(argv):
    # if input arguments were provided, override ones set in constants.py
    handle_input_arguments()
    print_constants()

    # log in to object storage and get a list of value tupples
    client = try_admin_login(constants.OBJSTOR_ADMIN, constants.OBJSTOR_ADMIN_PASS, constants.OBJSTOR_MGMT_ENDPOINT)
    if client is None:
        print("Unable to get bucket data from Object Storage Management API.")
        return

    buckets_dict = get_buckets(constants.OBJSTOR_MGMT_NAMESPACE, client)

    # The below function will print all bucket tags to console.
    save_bucket_details(buckets_dict)


if __name__ == "__main__":
    main(sys.argv[1:])
