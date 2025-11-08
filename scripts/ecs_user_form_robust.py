
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import os
import time
import random
import string

# Load environment variables
load_dotenv()
mgmt_url = os.getenv("MGMT_URL")

# Generate a 40-character secret key
def generate_secret_key(length=40):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))

# Set up Chrome options
options = Options()
options.add_argument("--start-maximized")

# Initialize WebDriver
driver = webdriver.Chrome(options=options)

try:
    # Prompt for credentials and ECS user info
    print("Please enter your credentials in the terminal window.")
    email = input("Enter your BC Gov email address: ")
    from getpass import getpass
    password = getpass("Enter your IDIR password: ")
    ecs_username = input("Enter the ECS username to create: ")
    secret_key = generate_secret_key()

    # Navigate to ECS Management Console
    driver.get(mgmt_url)

    # Wait for login fields and enter credentials
    user_field = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, "//input[@type='text' or @type='email']"))
    )
    pass_field = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, "//input[@type='password']"))
    )
    user_field.send_keys(email)
    pass_field.send_keys(password)

    # Click the login button
    login_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn.btn-primary.btn-large"))
    )
    login_button.click()

    # Wait for Users page to load and click "Users"
    users_link = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH, "//a[normalize-space()='Users']"))
    )
    users_link.click()

    # Wait for New Object User button and click it
    new_user_button = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'New Object User')]"))
    )
    new_user_button.click()

    # Wait for the form fields to appear
    username_field = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, "//input[@ng-model='user.userId']"))
    )
    namespace_field = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, "//input[@ng-model='user.namespace']"))
    )
    secret_key_field = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, "//input[@ng-model='user.secretKey']"))
    )

    # Fill in the form
    username_field.send_keys(ecs_username)
    namespace_field.clear()
    namespace_field.send_keys("nrs")
    secret_key_field.send_keys(secret_key)

    print(f"User form filled for '{ecs_username}' with generated secret key.")
    input("Press Enter to close the browser...")

except Exception as e:
    print("Error during automation:", e)

finally:
    driver.quit()
