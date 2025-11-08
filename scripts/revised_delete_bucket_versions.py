{
    "chunks": [
        {
            "type": "txt",
            "chunk_number": 1,
            "lines": [
                {
                    "line_number": 1,
                    "text": "# -------------------------------------------------------------------------------"
                },
                {
                    "line_number": 2,
                    "text": "# Name:        delete_bucket_versions.py"
                },
                {
                    "line_number": 3,
                    "text": "# Purpose:     the purpose of the script is to scan an object storage bucket for"
                },
                {
                    "line_number": 4,
                    "text": "#              filenames and delete extra versions of files:"
                },
                {
                    "line_number": 5,
                    "text": "#              1.) you will need an .env file for key/value pairs and a constant.py file to successfully run this script"
                },
                {
                    "line_number": 6,
                    "text": "#              2.) connect to S3 Object Storage bucket"
                },
                {
                    "line_number": 7,
                    "text": "#              3.) read object keys to list"
                },
                {
                    "line_number": 8,
                    "text": "#              4.) iterate over list, write file names with excess versions to a file"
                },
                {
                    "line_number": 9,
                    "text": "#              5.) get confirmation to delete excess versions"
                },
                {
                    "line_number": 10,
                    "text": "#              5.) delete excess file versions"
                },
                {
                    "line_number": 11,
                    "text": "#"
                },
                {
                    "line_number": 12,
                    "text": "# Author:      HHAY, PPLATTEN"
                },
                {
                    "line_number": 13,
                    "text": "#"
                },
                {
                    "line_number": 14,
                    "text": "# Created:     2024-03-11"
                },
                {
                    "line_number": 15,
                    "text": "# Copyright:   (c) OPTIMIZATION TEAM 2024"
                },
                {
                    "line_number": 16,
                    "text": "# Licence:     mine"
                },
                {
                    "line_number": 17,
                    "text": "#"
                },
                {
                    "line_number": 18,
                    "text": "#"
                },
                {
                    "line_number": 19,
                    "text": "# usage: 'delete_bucket_versions.py"
                },
                {
                    "line_number": 20,
                    "text": "# example: 'delete_bucket_versions.py'"
                },
                {
                    "line_number": 21,
                    "text": "# -------------------------------------------------------------------------------"
                },
                {
                    "line_number": 22,
                    "text": ""
                },
                {
                    "line_number": 23,
                    "text": "# import python libraries"
                },
                {
                    "line_number": 24,
                    "text": "from time import sleep"
                },
                {
                    "line_number": 25,
                    "text": "import boto3"
                },
                {
                    "line_number": 26,
                    "text": "import constants"
                },
                {
                    "line_number": 27,
                    "text": ""
                },
                {
                    "line_number": 28,
                    "text": ""
                },
                {
                    "line_number": 29,
                    "text": "while True:"
                },
                {
                    "line_number": 30,
                    "text": "# create a client with S3, the access key, secret key, and public endpoint."
                },
                {
                    "line_number": 31,
                    "text": "s3_client = boto3.client("
                },
                {
                    "line_number": 32,
                    "text": "\"s3\","
                },
                {
                    "line_number": 33,
                    "text": "aws_access_key_id=constants.AWS_ACCESS_KEY_ID,"
                },
                {
                    "line_number": 34,
                    "text": "aws_secret_access_key=constants.AWS_SECRET_ACCESS_KEY,"
                },
                {
                    "line_number": 35,
                    "text": "endpoint_url=constants.AWS_S3_ENDPOINT,"
                },
                {
                    "line_number": 36,
                    "text": ")"
                },
                {
                    "line_number": 37,
                    "text": ""
                },
                {
                    "line_number": 38,
                    "text": "bucket = constants.AWS_S3_BUCKET"
                },
                {
                    "line_number": 39,
                    "text": ""
                },
                {
                    "line_number": 40,
                    "text": "# placeholder list for the filenames"
                },
                {
                    "line_number": 41,
                    "text": "filenames = []"
                },
                {
                    "line_number": 42,
                    "text": ""
                },
                {
                    "line_number": 43,
                    "text": "# get a list of bucket file names"
                },
                {
                    "line_number": 44,
                    "text": "def get_filenames(s3_client):"
                },
                {
                    "line_number": 45,
                    "text": ""
                },
                {
                    "line_number": 46,
                    "text": "# get first 1000 objects"
                },
                {
                    "line_number": 47,
                    "text": "result = s3_client.list_object_versions(Bucket=bucket)"
                },
                {
                    "line_number": 48,
                    "text": "# put all objects into a dictionary, with the value as a counter"
                },
                {
                    "line_number": 49,
                    "text": "keyCount = {}"
                },
                {
                    "line_number": 50,
                    "text": "for item in result[\"Versions\"]:"
                },
                {
                    "line_number": 51,
                    "text": "if item[\"Key\"] not in keyCount:"
                },
                {
                    "line_number": 52,
                    "text": "keyCount[item[\"Key\"]] = 1"
                },
                {
                    "line_number": 53,
                    "text": "else:"
                },
                {
                    "line_number": 54,
                    "text": "keyCount[item[\"Key\"]] += 1"
                },
                {
                    "line_number": 55,
                    "text": ""
                },
                {
                    "line_number": 56,
                    "text": "# if there are more than 1000 results, repeat the process until there are no extras"
                },
                {
                    "line_number": 57,
                    "text": "continuationToken = result[\"NextKeyMarker\"] if \"NextKeyMarker\" in result else None"
                },
                {
                    "line_number": 58,
                    "text": "while continuationToken:"
                },
                {
                    "line_number": 59,
                    "text": "print(continuationToken)"
                },
                {
                    "line_number": 60,
                    "text": "result = s3_client.list_object_versions(Bucket=bucket,KeyMarker=continuationToken)"
                },
                {
                    "line_number": 61,
                    "text": "if \"Versions\" in result:"
                },
                {
                    "line_number": 62,
                    "text": "for item in result[\"Versions\"]:"
                },
                {
                    "line_number": 63,
                    "text": "if item[\"Key\"] not in keyCount:"
                },
                {
                    "line_number": 64,
                    "text": "keyCount[item[\"Key\"]] = 1"
                },
                {
                    "line_number": 65,
                    "text": "else:"
                },
                {
                    "line_number": 66,
                    "text": "keyCount[item[\"Key\"]] += 1"
                },
                {
                    "line_number": 67,
                    "text": "else:"
                },
                {
                    "line_number": 68,
                    "text": "if item[\"Key\"] not in keyCount:"
                },
                {
                    "line_number": 69,
                    "text": "keyCount[item[\"Key\"]] = 1"
                },
                {
                    "line_number": 70,
                    "text": "else:"
                },
                {
                    "line_number": 71,
                    "text": "keyCount[item[\"Key\"]] += 1"
                },
                {
                    "line_number": 72,
                    "text": "continuationToken = result[\"NextKeyMarker\"] if \"NextKeyMarker\" in result else None"
                },
                {
                    "line_number": 73,
                    "text": "return keyCount"
                },
                {
                    "line_number": 74,
                    "text": ""
                },
                {
                    "line_number": 75,
                    "text": "list_file_names = get_filenames(s3_client)"
                },
                {
                    "line_number": 76,
                    "text": ""
                },
                {
                    "line_number": 77,
                    "text": "# set a maximum amount of versions for each file"
                },
                {
                    "line_number": 78,
                    "text": "maximum_versions = 300"
                },
                {
                    "line_number": 79,
                    "text": "# reduce the list of file names to only keys with over the maximum count"
                },
                {
                    "line_number": 80,
                    "text": "list_file_names = {key: value for key, value in list_file_names.items() if value > maximum_versions}"
                },
                {
                    "line_number": 81,
                    "text": ""
                },
                {
                    "line_number": 82,
                    "text": "# name the text file that is saved to your output folder"
                },
                {
                    "line_number": 83,
                    "text": "outputname = f\"{bucket}_filenames.txt\""
                },
                {
                    "line_number": 84,
                    "text": "# write the list of filenames and file counts to a text file"
                },
                {
                    "line_number": 85,
                    "text": "def write_list(list={}):"
                },
                {
                    "line_number": 86,
                    "text": "with open(r\"C:/Git_Repo/Output/\" + outputname, \"w\") as f: # change the folder path to suit your needs"
                },
                {
                    "line_number": 87,
                    "text": "for line in list:"
                },
                {
                    "line_number": 88,
                    "text": "f.write(line+','+str(list[line]))"
                },
                {
                    "line_number": 89,
                    "text": "f.write(\"\\n\")"
                },
                {
                    "line_number": 90,
                    "text": "write_list(list_file_names)"
                },
                {
                    "line_number": 91,
                    "text": ""
                },
                {
                    "line_number": 92,
                    "text": "# allow user to check the text file before confirming delete"
                },
                {
                    "line_number": 93,
                    "text": "confirm = input(\"Confirm Delete (Y/N):\")"
                },
                {
                    "line_number": 94,
                    "text": "if confirm.capitalize()==\"Y\":"
                },
                {
                    "line_number": 95,
                    "text": ""
                },
                {
                    "line_number": 96,
                    "text": "# for each object with over maximum_versions"
                },
                {
                    "line_number": 97,
                    "text": "for line in list_file_names:"
                },
                {
                    "line_number": 98,
                    "text": "# get all versions of that object"
                },
                {
                    "line_number": 99,
                    "text": "result = s3_client.list_object_versions(Bucket=bucket,Prefix=line)"
                },
                {
                    "line_number": 100,
                    "text": "delete_objects=[]"
                },
                {
                    "line_number": 101,
                    "text": "counter = 0"
                },
                {
                    "line_number": 102,
                    "text": "for item in result[\"Versions\"]:"
                },
                {
                    "line_number": 103,
                    "text": "# if counter < maximum_versions:"
                },
                {
                    "line_number": 104,
                    "text": "if counter < 5:"
                },
                {
                    "line_number": 105,
                    "text": "counter+=1"
                },
                {
                    "line_number": 106,
                    "text": "continue"
                },
                {
                    "line_number": 107,
                    "text": "# after skipping the allowed versions, create dict of versions to delete"
                },
                {
                    "line_number": 108,
                    "text": "delete_objects.append({\"Key\":line,\"VersionId\":item[\"VersionId\"]})"
                },
                {
                    "line_number": 109,
                    "text": "print(f\"Deleting {len(delete_objects)} from {line}\")"
                },
                {
                    "line_number": 110,
                    "text": "# delete unwanted versions"
                },
                {
                    "line_number": 111,
                    "text": "result = s3_client.delete_objects(Bucket=bucket,Delete={'Objects': delete_objects})"
                },
                {
                    "line_number": 112,
                    "text": "print(f\"Deleted {len(result['Deleted'])} from {line}\")"
                },
                {
                    "line_number": 113,
                    "text": "print(\"Sleeping...\")"
                },
                {
                    "line_number": 114,
                    "text": "sleep(600)"
                }
            ],
            "token_count": 985
        }
    ]
}
