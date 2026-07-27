# -------------------------------------------------------------------------------
# Name:        set_s3_bucket_cors.py
# Purpose:     This script gets or sets a CORS setting for an object storage bucket
#
# Author:      Peter Platten
#
# Created:     2024
# Copyright:   (c) Peter Platten & Optimization Team 2024
# Licence:     mine
#
# Notes:       see https://docs.aws.amazon.com/AmazonS3/latest/userguide/ManageCorsUsing.html
#
# -------------------------------------------------------------------------------

from botocore.exceptions import ClientError
from boto3_helpers.auth import get_client
from boto3_helpers.security import get_bucket_cors, set_bucket_cors, sample_cors_configuration
from utilities.file_helper import write_dict_to_new_file, open_file_in_notepad, create_dict_from_file
from utilities.log_helper import LOGGER
from constants import BUCKET_NAME, TEMP_DIR
import os

try:

    # Get the service client with sigv4 configured    
    s3_client = get_client()

    # Get pre-existing CORS Rules
    old_cors = get_bucket_cors(s3_client, BUCKET_NAME)
    if old_cors is None:
        confirm = input(f"Bucket {BUCKET_NAME} has no current CORS configuration. Open default configuration for edit? (Y/N):")
        if confirm.capitalize()=="Y":
            old_cors = sample_cors_configuration
        else:
            exit()
    
    temp_file_path = os.path.join(TEMP_DIR,f"{BUCKET_NAME}_cors.txt")
    write_dict_to_new_file(temp_file_path, old_cors)

    # Open the file for editing
    open_file_in_notepad(temp_file_path)

    # Wait for file close    
    confirm = input(f"Make desired changes in notepad. Once saved, enter Y/N to upload. Upload? (Y/N):")
    if confirm.capitalize()=="Y":
        # Update CORS
        new_cors = create_dict_from_file(temp_file_path)
        set_bucket_cors(s3_client, BUCKET_NAME, new_cors)
    
    # Display newly applied rules
    LOGGER.info("New CORS:")
    LOGGER.info(get_bucket_cors(s3_client, BUCKET_NAME))


except ClientError as e:
    LOGGER.error(e)

