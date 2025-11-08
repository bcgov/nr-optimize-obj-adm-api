import os
import time
import random
import string
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from getpass import getpass

# Load environment variables
load_dotenv()
mgmt_url = os.getenv("MGMT_URL")

# Prompt for credentials and custom username
email = input("Enter your BC Gov email address: ")
password = getpass("Enter your IDIR password: ")
custom_username = input("Enter the desired ECS Object Storage username: ")
bucket_name = input("Enter the desired bucket name: ")

# Prompt for bucket tag values
tags = {
    "Project": input("Enter value for Project: "),
    "Credential Holder": input("Enter value for Credential Holder: "),
    "Ministry": input("Enter value for Ministry: "),
    "Division": input("Enter value for Division: "),
    "Branch": input("Enter value for Branch: "),
    "Data Custodian": input("Enter value for Data Custodian: "),
    "Data Steward": input("Enter value for Data Steward: "),
    "GeoDrive": input("Enter value for GeoDrive: ")
}

# Generate a 40-character secret key
def generate_secret_key(length=40):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))

secret_key = generate_secret_key()

# Set up Chrome options
options = Options()
options.add_argument("--start-maximized")

# Initialize WebDriver
driver = webdriver.Chrome(options=options)
driver.get(mgmt_url)

try:
    # Wait for login fields and enter credentials
    user_field = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, "//input[@type='text' or @type='email']"))
    )
    pass_field = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, "//input[@type='password']"))
    )
    user_field.send_keys(email)
    pass_field.send_keys(password)

    login_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn.btn-primary.btn-large"))
    )
    login_button.click()

    # Wait for dashboard to load and click "Users"
    users_link = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Users')]"))
    )
    users_link.click()

    # Click "New Object User"
    new_user_button = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'New Object User')]"))
    )
    new_user_button.click()

    # Fill in the user creation form
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//input[@ng-model='user.userId']"))
    ).send_keys(custom_username)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//input[@ng-model='user.namespace']"))
    ).send_keys("nrs")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//input[@ng-model='user.secretKey']"))
    ).send_keys(secret_key)

    # Submit the user creation form
    create_user_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Create')]"))
    )
    create_user_button.click()

    # Wait for user creation to complete and navigate to Buckets
    buckets_link = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Buckets')]"))
    )
    buckets_link.click()

    # Click "New Bucket"
    new_bucket_button = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'New Bucket')]"))
    )
    new_bucket_button.click()

    # Fill in bucket name
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//input[@ng-model='bucket.name']"))
    ).send_keys(bucket_name)

    # Set owner
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//input[@ng-model='bucket.owner']"))
    ).send_keys(custom_username)

    # Enable metadata search
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//input[@ng-model='bucket.metadataSearchEnabled']"))
    ).click()

    # Enable access during outage
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//input[@ng-model='bucket.accessDuringOutage']"))
    ).click()

    # Fill in tags
    for key, value in tags.items():
        tag_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, f"//input[@placeholder='{key}']"))
        )
        tag_input.send_keys(value)

    # Submit the bucket creation form
    create_bucket_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Create')]"))
    )
    create_bucket_button.click()

    print("User and bucket created successfully.")
    input("Press Enter to close the browser...")

except Exception as e:
    print("Error during automation:", e)

finally:
    driver.quit()
