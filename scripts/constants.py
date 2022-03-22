import os
import dotenv

envPath = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(envPath):
    print("loading dot env...")
    dotenv.load_dotenv()

BUCKET_NAME = os.environ['BUCKET_NAME']
BUCKET_USER = os.environ['BUCKET_USER']
BUCKET_SECRET = os.environ['BUCKET_SECRET']

OBJSTOR_ACCESS_KEY = os.environ['OBJSTOR_ACCESS_KEY']
OBJSTOR_SECRET_KEY = os.environ['OBJSTOR_SECRET_KEY']
OBJSTOR_BUCKET = os.environ['OBJSTOR_BUCKET']
OBJSTOR_ENDPOINT = os.environ['OBJSTOR_ENDPOINT']
OPENSHIFT_NAMESPACE = os.environ['OPENSHIFT_NAMESPACE']
OPENSHIFT_PVC = os.environ['OPENSHIFT_PVC']

AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
AWS_S3_ENDPOINT = os.environ['AWS_S3_ENDPOINT']
AWS_S3_BUCKET = os.environ['AWS_S3_BUCKET']
