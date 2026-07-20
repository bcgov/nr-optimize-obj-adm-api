# -------------------------------------------------------------------------------
# Name:        list_bucket_files.py
# Purpose:     the purpose of the script is to scan an object storage bucket for 
#              filenames and write them (if any) to a text document for review :
#              1.) you will need an .env file for key/value pairs and a constant.py file to successfully run this script
#              2.) connect to S3 Object Storage bucket
#              3.) read object keys to list
#              4.) iterate over list, write filenames to text file
#
# Author:      HHAY, PPLATTEN
#
# Created:     2023-08-09
# Copyright:   (c) OPTIMIZATION TEAM 2023
# Licence:     mine
#
#
# usage: 'list_bucket_files.py
# example: 'list_bucket_files.py'
# -------------------------------------------------------------------------------

# import python libraries
import boto3
import constants


# create a client with S3, the access key, secret key, and public endpoint.
s3_client = boto3.client(
    "s3",
    aws_access_key_id=constants.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=constants.AWS_SECRET_ACCESS_KEY,
    endpoint_url=constants.AWS_S3_ENDPOINT,
)

bucket = constants.AWS_S3_BUCKET

# placeholder list for the filenames
filenames = []


# get a list of bucket file names
def get_filenames(s3_client):
    result = s3_client.list_objects_v2(Bucket=bucket)
    for item in result["Contents"]:
        files = item["Key"]
        print(files)
        filenames.append(files)
    return filenames


list_file_names = get_filenames(s3_client)

# name the text file that is saved to your output folder
outputname = f"{bucket}_filenames.txt"


# write the list of filenames to a text file
def write_list(list=[]):
    with open(r"C:/Git_Repo/Output/" + outputname, "w") as f: # change the folder path to suit your needs
        for line in list:
            f.write(line)
            f.write("\n")


write_list(list_file_names)
