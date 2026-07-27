
import boto3
from botocore.exceptions import ClientError
from utilities.log_helper import LOGGER

# Retrieve the CORS configuration
def get_bucket_cors(s3_client, bucket_name):
    try:
        response = s3_client.get_bucket_cors(Bucket=bucket_name)
        if "CORSRules" in response:
            response = response["CORSRules"][0]
        return response
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchCORSConfiguration':
            LOGGER.info(f"No CORS Rules are currently set on {bucket_name}.")
            return None
        else:
            # AllAccessDisabled error == bucket not found
            LOGGER.error(e)

# Set a CORS configuration
def set_bucket_cors(s3_client, bucket_name, cors_configuration: dict):

    try:
        if "CORSRules" not in cors_configuration:
            cors_configuration = {"CORSRules": cors_configuration} 
        new_config = sample_cors_configuration
        for key in sample_cors_configuration['CORSRules'][0]:
            new_config['CORSRules'][0][key] = cors_configuration['CORSRules'][key]
        s3_client.put_bucket_cors(Bucket=bucket_name, CORSConfiguration=new_config)    
    except ClientError as e:        
        LOGGER.error(e)

# AllowedOrigins should never use a wildcard
sample_cors_configuration = {
    'CORSRules': [{
        'AllowedHeaders': ['*'],
        'AllowedMethods': ['HEAD', 'GET', 'PUT', 'POST', 'DELETE'],
        'AllowedOrigins': [],
        'ExposeHeaders': ['ETag', 'x-amz-request-id','Access-Control-Allow-Origin'],
        'MaxAgeSeconds': 3000
    }]
}