import glob
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from chromedriver_py import binary_path

load_dotenv()

SELENIUM_SESSION_FILE = "./selenium_session"
SELENIUM_PORT = 9515
LOCAL_USER = os.getenv("LOCAL_USER")


class _Browser:
    BY = By

    def __init__(self, reuse_window=False):
        os.system("taskkill /f /im chrome.exe")
        options = webdriver.ChromeOptions()
        options.add_argument("--log-level=3")
        options.add_experimental_option("detach", True)
        options.add_argument("--disable-infobars")
        # options.add_argument("--enable-file-cookies")
        # options.add_experimental_option("excludeSwitches", ["enable-automation"])
        profile_path = rf"C:\Users\{LOCAL_USER}\AppData\Local\Google\Chrome\User Data"
        profile_name = "Profile 1"
        profiles = glob.glob(f"{profile_path}/Profile*")
        if len(profiles) > 1:
            profile_name = profiles[-1].split(os.sep)[-1]
            print(
                f'Warning: multiple Chrome profiles found. Using {profile_name}, if this is incorrect, add e.g. "CHROME_PROFILE = Profile 1" to .env'
            )
        else:
            profile_name = "Profile 1"
        options.add_argument(f"--user-data-dir={profile_path}")
        options.add_argument(f"--profile-directory={profile_name}")
        # options.add_argument('--remote-debugging-port=9222')
        svc = webdriver.ChromeService(
            executable_path=binary_path,
            port=SELENIUM_PORT,
            capabilities=options.to_capabilities(),
        )

        if reuse_window and os.path.isfile(SELENIUM_SESSION_FILE):
            session_file = open(SELENIUM_SESSION_FILE)
            session_info = session_file.readlines()
            session_file.close()

            executor_url = session_info[0].strip()
            session_id = session_info[1].strip()

            self.driver = webdriver.Remote(
                command_executor=executor_url, options=options
            )
            self.driver.close()
            self.driver.quit()

            self.driver.session_id = session_id
        else:
            # options.add_argument("--headless=old")

            # options.add_experimental_option('useAutomationExtension', False)
            # options.add_argument('--disable-infobars')
            # options.add_argument('--disable-dev-shm-usage')
            # options.add_argument('--no-sandbox')
            # options.add_argument('--remote-debugging-port=9222')
            # svc = webdriver.ChromeService(executable_path="C:\Program Files\Google\Chrome\Application\chrome.exe")

            options.add_experimental_option("detach", True)
            self.driver = webdriver.Chrome(service=svc, options=options)
            if reuse_window:
                session_file = open(SELENIUM_SESSION_FILE, "w")
                session_file.writelines(
                    [
                        self.driver.command_executor._url,
                        "\n",
                        self.driver.session_id,
                        "\n",
                    ]
                )
                session_file.close()

    def get_url_source(self, url):
        self.driver.get(url)
        self.driver.minimize_window()
        if "Log in" in self.driver.page_source:
            raise Exception(
                "Session has expired, please log in manually in Chrome first"
            )
        return BeautifulSoup(self.driver.page_source, features="html.parser")

    def wait_for_page_item(self, by, item, seconds=1):
        # self.get_url_source(url)
        WebDriverWait(self.driver, seconds).until(
            EC.presence_of_element_located((by, item))
        )
        return BeautifulSoup(
            self.driver.find_element(by, item).get_attribute("innerHTML"),
            features="html.parser",
        )


class Browser:
    def __init__(self):
        self.browser = None

    def get_browser(self, reuse_window=False):
        if not self.browser:
            self.browser = _Browser(reuse_window)
        return self.browser
