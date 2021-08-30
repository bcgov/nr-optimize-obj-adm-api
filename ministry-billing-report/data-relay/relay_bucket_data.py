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
# -------------------------------------------------------------------------------

import datetime

import argparse
import constants
import os
import psycopg2
import smtplib
import socket
import sys
import time

from ecsclient.common.exceptions import ECSClientException
from ecsclient.client import Client
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


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


# Send an email to the admin with error message
def send_admin_email(message_detail):
    msg = MIMEMultipart("related")
    msg["Subject"] = "Script Report"
    if constants.DEBUG_EMAIL == "":
        msg["From"] = "IITD.Optimize@gov.bc.ca"
        msg["To"] = "IITD.Optimize@gov.bc.ca"
    else:
        msg["To"] = constants.DEBUG_EMAIL
        msg["From"] = constants.DEBUG_EMAIL
    html = (
        """<html><head></head><body><p>
        A scheduled script relay_bucket_data.py has sent an automated report email. Detailed Message:<br />"""
        + str(message_detail)
        + """</p></body></html>"""
    )
    msg.attach(MIMEText(html, "html"))
    s = smtplib.SMTP(constants.SMTP_SERVER)
    s.sendmail(msg["From"], msg["To"], msg.as_string())
    s.quit()


def try_admin_login(user, password, endpoint):
    client = None
    counter = 4
    while counter > 0:
        try:
            client = admin_login(constants.OBJSTOR_ADMIN, constants.OBJSTOR_ADMIN_PASS, constants.OBJSTOR_MGMT_ENDPOINT)
            counter = 0
        except ECSClientException as ecsclient_ex:
            if ecsclient_ex.message == 'Invalid username or password':
                dir_path = os.path.dirname(os.path.realpath(__file__))
                host_name = socket.gethostname()
                message_detail = "The Relay Bucket Data script failed to sign in to Object Storage Management " \
                    + "API due to an invalid username or password error.<br />" \
                    + "<br />Username: " + constants.OBJSTOR_ADMIN \
                    + "<br />Server: " + str(host_name) \
                    + "<br />File Path: " + dir_path
                send_admin_email(message_detail)
                counter = 0
                pass
            elif counter == 1:
                print("Connection to S3 Failed, closing")
                host_name = socket.gethostname()
                message_detail = "The Relay Bucket Data script failed to sign in to Object Storage Management " \
                    + "API with the following message.<br />" \
                    + "<br />Message: " + ecsclient_ex.message \
                    + "<br />Message Detail: " + ecsclient_ex.message_detail \
                    + "<br />Username: " + constants.OBJSTOR_ADMIN \
                    + "<br />Server: " + str(host_name) \
                    + "<br />File Path: " + dir_path
                send_admin_email(message_detail)
            else:
                print("Connection to S3 Failed, trying again in 10")
                time.sleep(10)
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
    sample_date = datetime.date.today()
    for bucket in bucket_list:
        bucket_response = client.bucket.getbucketdetails(namespace, bucket["name"])
        bucket_response["owner"] = bucket["owner"]
        bucket_response["softquota"] = bucket["softquota"]
        bucket_response["notification_size"] = bucket["notification_size"]
        bucket_response["created"] = datetime.datetime.strptime(bucket['created'].split('T')[0], '%Y-%m-%d')
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
    parser.add_argument(
        "-postgres_user",
        "--postgres_user",
        dest="postgres_user",
        required=False,
        help="posgress account for accessing metabase postgress database",
        metavar="string",
        type=str
    )
    parser.add_argument(
        "-postgres_pass",
        "--postgres_pass",
        dest="postgres_pass",
        required=False,
        help="postgress password for accessing metabase postgress database",
        metavar="string",
        type=str
    )

    args = parser.parse_args()

    # Override constants
    if args.objstor_admin is not None:
        constants.OBJSTOR_ADMIN = args.objstor_admin
    if args.objstor_pass is not None:
        constants.OBJSTOR_ADMIN_PASS = args.objstor_pass
    if args.postgres_user is not None:
        constants.POSTGRES_USER = args.postgres_user
    if args.postgres_pass is not None:
        constants.POSTGRES_PASS = args.postgres_pass


def update_database(buckets_dict):
    conn = None
    try:
        # Open a connection
        # Note - server_side_manager.bat BINDS the pods postgres port to localhost
        conn = psycopg2.connect(
            host="localhost",
            database=constants.POSTGRES_DB_NAME,
            user=constants.POSTGRES_USER,
            password=constants.POSTGRES_PASS
        )
        # create a cursor
        cur = conn.cursor()

        # get all bucket metadata
        cur.execute

        # build data
        watermark_tups = []
        bucket_tups = []
        for bucket_name in buckets_dict:
            bucket = buckets_dict[bucket_name]
            watermark_tup = (bucket['name'], bucket['sample_date'], bucket['total_size'])
            watermark_tups.append(watermark_tup)
            bucket_tup = (
                bucket['name'],
                bucket['owner'],
                bucket['organization'],
                bucket['project'],
                bucket['custodian'],
                bucket['steward']
            )
            bucket_tups.append(bucket_tup)

        # upsert bucket metadata table
        print('Upserting bucket metadata')
        cur.executemany('''
            INSERT INTO bucketwatermarklookup (bucketname, ownerusername, organization, project, custodian, steward)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (bucketname) DO UPDATE SET
            (ownerusername, organization, project, custodian, steward)
            = (EXCLUDED.ownerusername, EXCLUDED.organization, EXCLUDED.project, EXCLUDED.custodian, EXCLUDED.steward);
        ''', bucket_tups)
        print('Upsert Complete')

        # insert watermark data
        print('Inserting watermark data...')
        cur.executemany("INSERT INTO bucketwatermarkmonthly(bucketname,date,watermarkgb) VALUES(%s,%s,%s)", watermark_tups)
        print('Insert Complete.')

        conn.commit()

        # close the communication with the PostgreSQL
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        host_name = socket.gethostname()
        dir_path = os.path.dirname(os.path.realpath(__file__))
        message_detail = "The Relay Bucket Data script failed to sign in to Submit data to POSTGRES Database." \
            + "Connection or insert failed with the following message.<br />" \
            + "<br />Message: " + error \
            + "<br />Username: " + constants.POSTGRES_USER \
            + "<br />Server: " + str(host_name) \
            + "<br />File Path: " + dir_path
        send_admin_email(message_detail)
    finally:
        if conn is not None:
            conn.close()
            print('Database connection closed.')


def print_constants():
    print("OBJSTOR_ADMIN: " + constants.OBJSTOR_ADMIN)
    print("OBJSTOR_ADMIN_PASS: " + constants.OBJSTOR_ADMIN_PASS)
    print("OBJSTOR_MGMT_ENDPOINT: " + constants.OBJSTOR_MGMT_ENDPOINT)
    print("OBJSTOR_MGMT_NAMESPACE: " + constants.OBJSTOR_MGMT_NAMESPACE)
    print("POSTGRES_DB_NAME: " + constants.POSTGRES_DB_NAME)
    print("POSTGRES_USER: " + constants.POSTGRES_USER)
    print("POSTGRES_PASS: " + constants.POSTGRES_PASS)


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

    # update the postgres database
    update_database(buckets_dict)
    print("Database Updated")


if __name__ == "__main__":
    main(sys.argv[1:])
