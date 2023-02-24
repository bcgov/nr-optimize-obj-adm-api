# -------------------------------------------------------------------------------
# Name:        bucket_extract_uppercase.py
# Purpose:     the purpose of the script is to scan an object storage bucket for uppercase
#              filenames and write them (if any) to a text document for review :
#              1.) you will need an .env file for key/value pairs and a constant.py file to successfully run this script
#              2.) connect to S3 Object Storage bucket
#              3.) read object keys to list
#              4.) iterate over list, write filenames containing uppercase to file
#
# Author:      HHAY, PPLATTEN
#
# Created:     2022-03-18
# Copyright:   (c) OPTIMIZATION TEAM 2022
# Licence:     mine
#
#
# usage: 'bucket_extract_uppercase.py
# example: 'bucket_extract_uppercase.py'
# -------------------------------------------------------------------------------

import boto3
import botocore
import constants
import re
import sys
from minio.error import S3Error


# Returns an array of file names in a bucket which have uppercase characters
def get_upper_filenames(s3: boto3.session.Session.resource):
    bucket_name = constants.AWS_S3_BUCKET

    s3_bucket = s3.Bucket(bucket_name)
    upper_files = []

    # Check that bucket exists.
    if s3_bucket.creation_date is None:
        print(f"Bucket {bucket_name} does not exist.")
        sys.exit()
    else:
        print(f"Bucket {bucket_name} exists. \n Parsing object keys for uppercase...\n")

    # This pattern matches any uppercase letters
    pattern = re.compile("[A-Z]")

    # Add all file names which match the pattern to a collection
    for s3_bucket_object in s3_bucket.objects.all():
        obj_key = s3_bucket_object.key
        if pattern.search(obj_key) is not None:
            upper_files.append(obj_key)

    return upper_files


# Writes a list to a file
def write_list(file_name, list=[]):
    with open(file_name, "w") as f:
        for line in list:
            f.write(line)
            f.write("\n")


# Returns true if there's an exact file name match in object storage
def file_exists_check(s3_client, file_name):
    try:
        s3_client.Object(constants.AWS_S3_BUCKET, file_name).load()
        return True
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        else:
            # Something else has gone wrong.
            raise


# Resolve a file conflict by copying a file to lowercase file name, then adding delete marker for original
def make_file_lowercase(s3_client, upper_file_name):
    bucket_name = constants.AWS_S3_BUCKET
    print(f"Lowercasing {upper_file_name}")
    s3_client.Object(bucket_name, upper_file_name.lower()).copy_from(
        CopySource=f"{bucket_name}/{upper_file_name}"
    )
    s3_client.Object(bucket_name, upper_file_name).delete()


def main():

    # Create a resource with S3, it's access key, secret key, and public endpoint.
    s3_client = boto3.resource(
        "s3",
        aws_access_key_id=constants.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=constants.AWS_SECRET_ACCESS_KEY,
        endpoint_url=constants.AWS_S3_ENDPOINT,
    )

    # Get an array of files with uppercase letters in their names
    upper_file_names = get_upper_filenames(s3_client)

    # Write the file names to a file
    bucket_name = constants.AWS_S3_BUCKET
    write_list(f"{bucket_name}_extract_uppercase.txt", upper_file_names)

    # pattern matches any uppercase letters optionally surrounded by any characters before a /
    uppercase_folder_pattern = re.compile(".*[A-Z].*/")

    # Check for conflicts in file name or folder name
    conflicted_files = set()
    uppercase_folders = set()
    uppercase_folder_files = set()
    for upper_name in upper_file_names:
        print(f"Found: {upper_name}")
        if file_exists_check(s3_client, upper_name.lower()):
            # There is a lowercase version of the file which conflicts
            conflicted_files.add(upper_name)
        elif uppercase_folder_pattern.search(upper_name) is not None:
            # If any of the files in this folder conflict we could cause folder conflict by only updating some files
            # Folder conflicts make GeoDrive unable to sync the entire contents of both folders
            uppercase_folder_files.add(upper_name)
            uppercase_folders.add(upper_name)
        else:
            # There are no possible conflicts, either in file name or folder path
            make_file_lowercase(s3_client, upper_name)

    # Find files which would be conflicted if we lowercased all folders.
    # i.e. if /FOLDER1/File1.txt and /Folder1/File1.txt both would not have been caught by a check for /folder1/file1.txt,
    # but if we lowercase both we would have to overwrite one. Conflict.
    lowercase_folder_files = set()
    conflicted_folder_files = []
    for upper_name in uppercase_folder_files:
        if upper_name.lower() in lowercase_folder_files:
            # file will be in conflict with others if we lowercase both folders
            conflicted_folder_files.append(upper_name)
        else:
            lowercase_folder_files.add(upper_name.lower())

    # Build a list of conflicted folders;
    # this is a list of folders which have children files which would conflict if we lowercased all files in the folder
    #       We cannot fix conflicts with shared "root" folders.
    #       i.e. for folder1/Folder2/Folder3
    #       We cannot lowercase any child of Folder2 without doing ALL of them,
    #       or we would create both folder1/folder2 and folder1/Folder2, creating GeoDrive folder Conflict
    #       In this case folder2 is what I've labelled "rootiest", as it is the folder closest to root which has an uppercase character

    # This pattern matches everything up to and including the first folder with an uppercase name
    # i.e. for folder1/Folder2/Folder3, it matches folder1/Folder2/
    rootiest_folder_pattern = re.compile("^[a-z0-9\\-. /]*[A-Z][\\w\\-. ]*/")

    conflicted_folders = set()
    for conflicted_file in conflicted_folder_files:
        rootiest_conflict_folder = rootiest_folder_pattern.findall(conflicted_file)[0]
        conflicted_folders.add(rootiest_conflict_folder.lower())
        print(f"Conflict detected for files in: {rootiest_conflict_folder}")

    # Rebuild the collection to collect a list of all conflicted files
    files_which_conflict = set()
    folder_conflict_files = set()
    for upper_name in uppercase_folder_files:
        if upper_name.lower() in conflicted_folder_files:
            # File would conflict if this and another uppercase file were lowercased
            files_which_conflict.add(upper_name)
            write_list(f"{bucket_name}_file_conflicts.txt", upper_file_names)
        elif any(folder in upper_name.lower() for folder in conflicted_folders):
            # File is in a folder which has an uppercase character, and the folder would conflict if only some children are made lowercase
            folder_conflict_files.add(upper_name)
            write_list(f"{bucket_name}_process_after_conflicts.txt", upper_file_names)
        else:
            make_file_lowercase(s3_client, upper_name)
    # write_list(f"{bucket_name}_file_conflicts.txt", upper_file_names)
    # write_list(f"{bucket_name}_process_after_conflicts.txt", upper_file_names)


if __name__ == "__main__":
    try:
        main()
    except S3Error as exc:
        print("error occurred.", exc)
