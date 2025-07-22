import os
import dotenv

envPath = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(envPath):
    print("loading dot env...")
    dotenv.load_dotenv()

OBJSTOR_ADMIN = os.environ["OBJSTOR_ADMIN"]
OBJSTOR_ADMIN_PASS = os.environ["OBJSTOR_ADMIN_PASS"]

OBJSTOR_MGMT_NAMESPACE = os.environ["OBJSTOR_MGMT_NAMESPACE"]
OBJSTOR_MGMT_ENDPOINT = os.environ["OBJSTOR_MGMT_ENDPOINT"]
OBJSTOR_REPLICATION_GROUP = os.environ["OBJSTOR_REPLICATION_GROUP"]
OBJSTOR_ENDPOINT = os.environ["OBJSTOR_ENDPOINT"]

# OPENSHIFT_NAMESPACE = os.environ["OPENSHIFT_NAMESPACE"]
# OPENSHIFT_PVC = os.environ["OPENSHIFT_PVC"]

ACCESS_KEY = os.environ["ACCESS_KEY"]
SECRET_KEY = os.environ["SECRET_KEY"]
S3_ENDPOINT = os.environ["S3_ENDPOINT"]
S3_BUCKET_NAME = os.environ["S3_BUCKET_NAME"]
