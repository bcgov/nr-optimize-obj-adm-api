import os
import dotenv

envPath = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(envPath):
    print("loading dot env...")
    dotenv.load_dotenv()

AWS_SERVER_PUBLIC_KEY = os.environ["AWS_SERVER_PUBLIC_KEY"]
AWS_SERVER_SECRET_KEY = os.environ["AWS_SERVER_SECRET_KEY"]
OBJSTOR_PUBLIC_ENDPOINT = os.environ["OBJSTOR_PUBLIC_ENDPOINT"]
