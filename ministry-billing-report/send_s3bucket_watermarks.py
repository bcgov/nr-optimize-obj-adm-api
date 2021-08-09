# -------------------------------------------------------------------------------
# Name:        get_S3bucket_watermarks.py
# Purpose:     login into the S3 DELL management, check all bucket sizes, save watermark.
#
# Author:      IITD Optimize Team, (PPLATTEN)
#
# Created:     2021-07-27
# dependent on https://github.com/EMCECS/python-ecsclient
# TODO: Verify bucket data is being imported correctly
# TODO: Run from OpenShift
# TODO: Push data to database instead of CSV?
# TODO: Currently script doesn't actually read old watermark data, it just dumps current to csv.
# -------------------------------------------------------------------------------

from datetime import datetime
import constants
import pandas as pd
import time
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from ecsclient.common.exceptions import ECSClientException
from ecsclient.client import Client

file_name = "watermark"


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


def create_bucket_dataframe(bucket):
    if "watermark" not in bucket:
        bucket["watermark"] = bucket["total_size"]
    return pd.DataFrame(
        {
            "bucket": [bucket["name"]],
            "owner_username": [bucket["owner"]],
            "created": [bucket["created"]],
            "organization": [bucket["organization"]],
            "project": [bucket["project"]],
            "custodian": [bucket["custodian"]],
            "steward": [bucket["steward"]],
            "watermark": [bucket["watermark"]],
            "bucket_size": [bucket["total_size"]]
        }
    )


# print all bucket sizes out of the bucket dictionary
def print_bucket(bucket):
    bucket_name = bucket["name"]
    bucket_size = bucket["total_size"]
    owner_username = bucket["owner"]
    bucket_project = bucket["project"]
    bucket_organization = bucket["org"]
    bucket_custodian = bucket["custodian"]
    bucket_steward = bucket["steward"]
    print(
        f"Bucket: {bucket_name}, Bucket Size: {bucket_size}, Owner Username: {owner_username}, " +
        f"Project: {bucket_project}, Organization: {bucket_organization}, Custodian: {bucket_custodian}, Steward: {bucket_steward}"
    )


# create a csv file dump of the buckets dictionary
def csv_bucket_watermarks(buckets):
    in_file_name = os.path.join(constants.WATERMARK_TEMP_DIR, f"{file_name}.csv")
    frame = pd.read_csv(in_file_name, low_memory=False)
    new_frame = None

    for bucket_name in buckets:
        read_frame = frame[frame["bucket"].isin([bucket_name])]
        bucket = buckets[bucket_name]

        # if bucket exists in the original csv, check old watermark
        if read_frame["bucket"].count() > 0:
            old_watermark = read_frame.iloc[0]["watermark"]
            current_size = float(bucket["total_size"])
            if current_size < old_watermark:
                bucket["watermark"] = old_watermark

        # add bucket data to a new frame
        temp_frame = create_bucket_dataframe(bucket)
        if new_frame is None:
            new_frame = temp_frame
        else:
            new_frame = pd.concat([new_frame, temp_frame])

    # save csv and return the path
    datetime_file_name = datetime.today().strftime('%Y-%m-%d-%H')
    new_path = os.path.join(constants.WATERMARK_TEMP_DIR, f"{file_name}_{datetime_file_name}.csv")
    new_frame.to_csv(
        new_path, header=True, index=False
    )
    return new_path


# note, doesn't actually send csv, just a notification so we'll know it's run in the pod.
# this would potentially eventually be expanded to send watermarks/estimates after last watermark for the month
def send_csv(recipient):
    msg = MIMEMultipart("related")
    msg["Subject"] = "Bucket Summary"
    msg["From"] = "IITD.Optimize@gov.bc.ca"
    msg["To"] = recipient
    html = (
        """\
    <html>
        <head></head>
        <body>
        <p>
            This script has sent a test email.
        </p>
        </body>
    </html>""")
    body = MIMEText(html, "html")
    msg.attach(body)
    s = smtplib.SMTP(constants.SMTP_SERVER)
    s.sendmail(msg["From"], recipient, msg.as_string())
    s.quit()
    print(f"Email sent to {recipient}.")


def main():
    # skip the bulk of the work until confirmed it's in the pod and runs, remove this env variable later
    if constants.SKIP_OBJSTOR.capitalize() == 'FALSE':
        client = adminLogin(constants.OBJSTOR_ADMIN, constants.OBJSTOR_ADMIN_PASS, constants.OBJSTOR_MGMT_ENDPOINT)
        # client = try_admin_login(constants.OBJSTOR_ADMIN, constants.OBJSTOR_ADMIN_PASS, constants.OBJSTOR_MGMT_ENDPOINT)
        if client is None:
            print("Unable to connect to S3")
            return
        # get a dictionary of bucket info by name
        buckets_dict = get_buckets(constants.OBJSTOR_MGMT_NAMESPACE, client)
        csv_path = csv_bucket_watermarks(buckets_dict)
        csv_path = csv_path
    send_csv(constants.DEBUG_EMAIL)


if __name__ == "__main__":
    main()
