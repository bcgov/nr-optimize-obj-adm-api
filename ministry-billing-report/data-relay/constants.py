import os
import dotenv

envPath = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(envPath):
    print("loading dot env...")
    dotenv.load_dotenv()


OBJSTOR_ADMIN = os.environ['OBJSTOR_ADMIN']
OBJSTOR_ADMIN_PASS = os.environ['OBJSTOR_ADMIN_PASS']
OBJSTOR_MGMT_ENDPOINT = os.environ['OBJSTOR_MGMT_ENDPOINT']
OBJSTOR_MGMT_NAMESPACE = os.environ['OBJSTOR_MGMT_NAMESPACE']
