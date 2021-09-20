import os
import dotenv

envPath = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(envPath):
    print("loading dot env...")
    dotenv.load_dotenv()

OBJSTOR_ACCESS_KEY = os.environ["OBJSTOR_ACCESS_KEY"]
OBJSTOR_SECRET_KEY = os.environ["OBJSTOR_SECRET_KEY"]
OBJSTOR_BUCKET = os.environ["OBJSTOR_BUCKET"]
OBJSTOR_ENDPOINT = os.environ["OBJSTOR_ENDPOINT"]


def print_constants():
    print(f"OBJSTOR_ACCESS_KEY: {OBJSTOR_ACCESS_KEY}")
    print(f"OBJSTOR_SECRET_KEY: {OBJSTOR_SECRET_KEY}")
    print(f"OBJSTOR_BUCKET: {OBJSTOR_BUCKET}")
    print(f"OBJSTOR_ENDPOINT: {OBJSTOR_ENDPOINT}")
