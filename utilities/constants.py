import os
from dotenv import load_dotenv, find_dotenv

envPath = find_dotenv(usecwd=True)
if envPath:
    load_dotenv(dotenv_path=envPath)

# ---- Email / SMTP Helper ----
SMTP_SERVER = os.getenv('SMTP_SERVER', '')
DEBUG_EMAIL = os.getenv('DEBUG_EMAIL', '')
FROM_EMAIL = os.getenv('FROM_EMAIL', '')

# ---- File Helper ----
TEMP_DIR = os.getenv('TEMP_DIR', '/tmp')

# ---- Logging Helper ----
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')