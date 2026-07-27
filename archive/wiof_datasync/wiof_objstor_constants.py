import os
import dotenv

envPath = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(envPath):
    print("loading dot env...")
    dotenv.load_dotenv()

ACCESS_KEY = os.environ["ACCESS_KEY"]
SECRET_KEY = os.environ["SECRET_KEY"]
BUCKET_NAME = os.environ["BUCKET_NAME"]
S3_HOSTNAME = os.environ["S3_HOSTNAME"]

ADMIN_EMAIL = os.environ["ADMIN_EMAIL"]
SMTP_SERVER = os.environ["SMTP_SERVER"]


def print_constants():
    print(f"ACCESS_KEY: {ACCESS_KEY}")
    print(f"SECRET_KEY: {SECRET_KEY}")
    print(f"BUCKET_NAME: {BUCKET_NAME}")
    print(f"S3_HOSTNAME: {S3_HOSTNAME}")
