import pyotp
import time
import datetime
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from helper import Helper 

class Connection:
    def __init__(self, params):
        self.prop = params

    def broker_login(self, KiteConnect):
        # Assign properties
        api_key = self.prop[0]
        secret_key = self.prop[1]
        user_id = self.prop[2]
        user_pass = self.prop[3]
        mfa_token = self.prop[4]

        kite = KiteConnect(api_key=api_key)

        # Initialize browser service
        service = webdriver.chrome.service.Service('./driver/chromedriver')
        service.start()
        options = webdriver.ChromeOptions()
        #options.add_argument('--headless')
        driver = webdriver.Remote(service.service_url, options=options)

        # Auto enter login information
        driver.get(kite.login_url())
        driver.implicitly_wait(10)

        # Username input
        username = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="userid"]'))
        )
        username.send_keys(user_id)

        # Password input
        password = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="password"]'))
        )
        password.send_keys(user_pass)

        driver.implicitly_wait(10)

        # Submit button
        submit = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="container"]/div/div/div[2]/form/div[4]/button'))
        )
        submit.click()

        # MFA / external TOTP
        totp = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="container"]/div[2]/div/div/form/div[1]/input'))
        )
        authkey = pyotp.TOTP(mfa_token)
        totp.send_keys(authkey.now())

        continue_btn = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="container"]/div[2]/div/div/form/div[2]/button'))
        )

        time.sleep(5)
        auth_date = datetime.datetime.now().strftime('%H');

        # Request token generation
        url = driver.current_url
        url_parts = url.split('request_token=')
        if len(url_parts) > 1:
            initial_token = url_parts[1]
            request_token = initial_token.split('&')[0]
            Helper.write_text_output('request_token' + '_' + auth_date + '.txt', request_token)
        else:
            # Handle the case when the 'request_token=' delimiter is not found
            print("Error: 'request_token=' not found in the URL")
            with open('./output/request_token' + '_' + auth_date + '.txt', 'r') as r_file:
                request_token = r_file.readline()
                r_file.close()

        # Access token generation
        data = kite.generate_session(request_token, api_secret=secret_key)
        access_token = data['access_token']
        Helper.write_text_output('access_token' + '_' + auth_date + '.txt', access_token)

        driver.quit()

        return kite, access_token
