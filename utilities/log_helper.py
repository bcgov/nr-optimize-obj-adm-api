import logging
from utilities.constants import LOG_LEVEL
from utilities.send_admin_email import send_admin_email

# Storage for all log messages
LOG_STORAGE = []

def get_logs():
    """Return all stored log messages."""
    return LOG_STORAGE

def clear_logs():
    """Clear all stored log messages."""
    LOG_STORAGE.clear()

# Collect all log messages in memory for later retrieval
class LogStorageHandler(logging.Handler):
    """Handler that collects all log messages into LOG_STORAGE for later retrieval."""
    def emit(self, record):
        log_message = self.format(record)
        LOG_STORAGE.append(log_message)

# Custom log handler that calls an external function (send_admin_email)
class CustomFunctionHandler(logging.Handler):
    def emit(self, record):
        # Format the log message using the handler's formatter
        log_message = self.format(record)
        # Call your external function with data from the log record
        send_admin_email(log_message)


formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(lineno)d - %(message)s')

# 1. Initialize the logger
LOGGER = logging.getLogger()
LOGGER.setLevel(LOG_LEVEL)

# 2. Setup StreamHandler (Console) has all logs
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)
LOGGER.addHandler(console_handler)

# 3. Store all logs in memory
storage_handler = LogStorageHandler()
storage_handler.setLevel(logging.DEBUG)
storage_handler.setFormatter(formatter)
LOGGER.addHandler(storage_handler)

# 3. Emails fire for ERROR and CRITICAL
email_handler = CustomFunctionHandler()
email_handler.setLevel(logging.ERROR)
# email_handler.addFilter(ExcludeDebugInfoAndWarningFilter())
email_handler.setFormatter(formatter)
LOGGER.addHandler(email_handler)