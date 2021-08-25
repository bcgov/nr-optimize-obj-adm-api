import os
import dotenv

envPath = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(envPath):
    print("loading dot env...")
    dotenv.load_dotenv()
else:
    print(".env file not found")

OBJSTOR_ACCESS_KEY = os.environ["OBJSTOR_ACCESS_KEY"]
OBJSTOR_SECRET_KEY = os.environ["OBJSTOR_SECRET_KEY"]
OBJSTOR_BUCKET = os.environ["OBJSTOR_BUCKET"]
OBJSTOR_ENDPOINT = os.environ["OBJSTOR_ENDPOINT"]
OPENSHIFT_NAMESPACE = os.environ["OPENSHIFT_NAMESPACE"]
OPENSHIFT_PVC = os.environ["OPENSHIFT_PVC"]
