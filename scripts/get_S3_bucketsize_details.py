# -------------------------------------------------------------------------------
# Name:        get_S3_bucketsize_details.py
# Purpose:     The purpose of the script is to access an Object Storage bucket
# 	           and create an Excel report on the size of top-level folders as well
#              as any subfolders. Script assumes you have your .env and constants.py
#              configured:
#              1.) Select output directory
#              2.) Connect to S3 & Bucket - list objects
# 	           3.) Pull names & sizes for main folders & subfolders
#              4.) Send data to dataframe, export to Excel
#
# Author:      HHAY
#
# Created:     2021-08-26
# Copyright:   (c) Optimization Team 2021
# Licence:     mine
#
#
# usage: get_S3_bucketsize_details.py -o <output_directory>
# example:  get_S3_bucketsize_details.py -i J:\Scripts\Python\Data
# -------------------------------------------------------------------------------

import constants
import argparse
import sys
import time
import pandas as pd
from pandas import ExcelWriter
from boto3 import client


def main(argv):
    # take a single output directory argument in
    # print ('Number of arguments:', len(sys.argv), 'arguments.')
    # print ('Argument List:', str(sys.argv))

    outputdirectory = ""
    syntaxcmd = "Insufficient number of commands passed: get_S3_bucketsize_details.py -o <output_directory>"

    if len(sys.argv) < 3:
        print(syntaxcmd)
        sys.exit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-o",
        "--output",
        dest="outputdirectory",
        required=True,
        help="path to directory containing output excel file",
        metavar="string",
        type=str,
    )
    args = parser.parse_args()

    outputdirectory = args.outputdirectory

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

    # connect to S3
    s3 = client(
        "s3",
        endpoint_url=OBJSTOR_PUBLIC_ENDPOINT,
        aws_access_key_id=AWS_SERVER_PUBLIC_KEY,
        aws_secret_access_key=AWS_SERVER_SECRET_KEY,
    )
    
    # get the current date and time
    timestamp = time.strftime("%Y%m%d-%H%M%S")

    # create empty list to hold variable values
    listOfMainFolder = []
    listOfMainFolderSize = []
    listofFullPath = []
    listofFullPathSize = []

    # connect to Object Storage Bucket
    resp = s3.list_objects_v2(Bucket="PUT YOUR BUCKET NAME HERE")

    for key in resp["Contents"]:
        # list key and size of folder
        mainfolder = key["Key"].split("/")[0]
        fullpath = key["Key"].rsplit("/", 1)[0]
        size_in_mb = key["Size"] / (1 << 20)
        size_in_gb = key["Size"] / (1 << 30)

        # read variable values into lists
        listOfMainFolder.append(mainfolder)
        listOfMainFolderSize.append(size_in_gb)
        listofFullPath.append(fullpath)
        listofFullPathSize.append(size_in_mb)

    # list to DataFrame, add columns, group by unique folder name & sum up the folder size to 2 decimal points
    listDataFrame = pd.DataFrame(list(zip(listOfMainFolder, listOfMainFolderSize)))
    listDataFrame.columns = ["Main Folder", "Folder Size GB"]
    listDataFrame = listDataFrame.groupby("Main Folder").sum("Folder Size GB")
    listDataFrame["Folder Size GB"] = listDataFrame["Folder Size GB"].round(2)

    listDataFrame1 = pd.DataFrame(list(zip(listofFullPath, listofFullPathSize)))
    listDataFrame1.columns = ["Subfolder", "Folder Size MB"]
    listDataFrame1 = listDataFrame1.groupby("Subfolder").sum("Folder Size MB")
    listDataFrame1["Folder Size MB"] = listDataFrame1["Folder Size MB"].round(2)

    # export to Excel, label the sheets
    with ExcelWriter((outputdirectory) + r"\\Bucket_Folder_Size_Report_" + (timestamp) + ".xlsx") as writer:
        listDataFrame.to_excel(writer, sheet_name="Main Folder Sizes")
        listDataFrame1.to_excel(writer, sheet_name="Subfolder Sizes")


if __name__ == "__main__":
    main(sys.argv[1:])
