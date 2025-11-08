import os
import time
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

# Prompt for credentials
username = input("Enter your BC Gov email address: ")
password = getpass("Enter your IDIR password: ")

# Set up Chrome options
options = Options()
options.add_argument("--start-maximized")

# Initialize WebDriver
driver = webdriver.Chrome(options=options)

# Navigate to the ECS Management Console
driver.get(mgmt_url)
time.sleep(5)  # Allow time for redirect

try:
    # Wait for the username and password fields to be present
    user_field = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, "//input[@type='text' or @type='email']"))
    )
    pass_field = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, "//input[@type='password']"))
    )

    print("Login fields found. Entering credentials...")
    user_field.send_keys(username)
    pass_field.send_keys(password)

    # Wait for and click the login button
    login_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn.btn-primary.btn-large"))
    )
    login_button.click()

    print("Login button clicked. Check the browser window.")
except Exception as e:
    print("Error during login:", e)

input('Press Enter to close the browser...')
