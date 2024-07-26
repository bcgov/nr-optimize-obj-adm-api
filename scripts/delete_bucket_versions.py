# -------------------------------------------------------------------------------
# Name:        delete_bucket_versions.py
# Purpose:     the purpose of the script is to scan an object storage bucket for 
#              filenames and delete extra versions of files:
#              1.) you will need an .env file for key/value pairs and a constant.py file to successfully run this script
#              2.) connect to S3 Object Storage bucket
#              3.) read object keys to list
#              4.) iterate over list, write file names with excess versions to a file
#              5.) get confirmation to delete excess versions
#              5.) delete excess file versions
#
# Author:      HHAY, PPLATTEN
#
# Created:     2024-03-11
# Copyright:   (c) OPTIMIZATION TEAM 2024
# Licence:     mine
#
#
# usage: 'delete_bucket_versions.py
# example: 'delete_bucket_versions.py'
# -------------------------------------------------------------------------------

# import python libraries
from time import sleep
import boto3
import constants


while True:
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

        # get first 1000 objects
        result = s3_client.list_object_versions(Bucket=bucket)
        # put all objects into a dictionary, with the value as a counter
        keyCount = {}
        for item in result["Versions"]:
            if item["Key"] not in keyCount:
                keyCount[item["Key"]] = 1
            else:
                keyCount[item["Key"]] += 1

        # if there are more than 1000 results, repeat the process until there are no extras
        continuationToken = result["NextKeyMarker"] if "NextKeyMarker" in result else None
        while continuationToken:   
            print(continuationToken)   
            result = s3_client.list_object_versions(Bucket=bucket,KeyMarker=continuationToken)
            if "Versions" in result:
                for item in result["Versions"]:
                    if item["Key"] not in keyCount:
                        keyCount[item["Key"]] = 1
                    else:
                        keyCount[item["Key"]] += 1
            else:
                if item["Key"] not in keyCount:
                    keyCount[item["Key"]] = 1
                else:
                    keyCount[item["Key"]] += 1
            continuationToken = result["NextKeyMarker"] if "NextKeyMarker" in result else None
        return keyCount

    list_file_names = get_filenames(s3_client)

    # set a maximum amount of versions for each file
    maximum_versions = 300
    # reduce the list of file names to only keys with over the maximum count
    list_file_names = {key: value for key, value in list_file_names.items() if value > maximum_versions}

    # name the text file that is saved to your output folder
    outputname = f"{bucket}_filenames.txt"
    # write the list of filenames and file counts to a text file
    def write_list(list={}):
        with open(r"C:/Git_Repo/Output/" + outputname, "w") as f: # change the folder path to suit your needs
            for line in list:
                f.write(line+','+str(list[line]))
                f.write("\n")
    write_list(list_file_names)

    # allow user to check the text file before confirming delete
    confirm = input("Confirm Delete (Y/N):")
    if confirm.capitalize()=="Y":

        # for each object with over maximum_versions
        for line in list_file_names:
            # get all versions of that object
            result = s3_client.list_object_versions(Bucket=bucket,Prefix=line)
            delete_objects=[]
            counter = 0
            for item in result["Versions"]:
                # if counter < maximum_versions:
                if counter < 5:
                    counter+=1
                    continue
                # after skipping the allowed versions, create dict of versions to delete
                delete_objects.append({"Key":line,"VersionId":item["VersionId"]})
            print(f"Deleting {len(delete_objects)} from {line}")
            # delete unwanted versions
            result = s3_client.delete_objects(Bucket=bucket,Delete={'Objects': delete_objects})
            print(f"Deleted {len(result['Deleted'])} from {line}")
    print("Sleeping...")
    sleep(600)