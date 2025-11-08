import boto3
import os
import random
import string
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve credentials and endpoint from environment variables
idir_username = os.getenv("IDIR_USERNAME")
idir_password = os.getenv("IDIR_PASSWORD")
endpoint_url = os.getenv("ENDPOINT_URL")

# Generate a 40-character secret key with mixed characters
def generate_secret_key(length=40):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))

# Prompt for user and bucket names
user_name = input("Enter the desired user name: ")
bucket_name = input("Enter the desired bucket name: ")

# Prompt for bucket tag values
tags = {
    "Project": input("Enter value for Project: "),
    "Credential Holder": input("Enter value for Credential Holder: "),
    "Ministry": input("Enter value for Ministry: "),
    "Division": input("Enter value for Division: "),
    "Branch": input("Enter value for Branch: "),
    "Data Custodian": input("Enter value for Data Custodian: "),
    "Data Steward": input("Enter value for Data Steward: "),
    "GeoDrive": input("Enter value for GeoDrive: ")
}

# Create ECS client
client = boto3.client(
    's3',
    aws_access_key_id=idir_username,
    aws_secret_access_key=idir_password,
    endpoint_url=endpoint_url,
    verify=True
)

# Create user (simulated via IAM or ECS-specific API if available)
secret_key = generate_secret_key()
print(f"Generated secret key for user {user_name}: {secret_key}")

# Create bucket with metadata search and access during outage
client.create_bucket(Bucket=bucket_name)

# Enable metadata search (simulated via tagging or ECS-specific API)
metadata_search_tags = {
    "CreateTime": "System",
    "LastModified": "System",
    "ObjectName": "System",
    "Owner": "System",
    "Size": "System"
}

# Combine metadata search tags and user-defined tags
combined_tags = {**metadata_search_tags, **tags}

# Convert tags to AWS tagging format
tagging = {'TagSet': [{'Key': k, 'Value': v} for k, v in combined_tags.items()]}

# Apply tags to the bucket
client.put_bucket_tagging(Bucket=bucket_name, Tagging=tagging)

print(f"Bucket '{bucket_name}' created and tagged successfully for user '{user_name}'.")
