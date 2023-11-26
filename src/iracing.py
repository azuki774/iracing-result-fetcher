import time
import datetime as dt
import os
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
import os
from pythonjsonlogger import jsonlogger

lg = logging.getLogger(__name__)
lg.setLevel(logging.DEBUG)
h = logging.StreamHandler()
h.setLevel(logging.DEBUG)
json_fmt = jsonlogger.JsonFormatter(
    fmt="%(asctime)s %(levelname)s %(name)s %(message)s", json_ensure_ascii=False
)
h.setFormatter(json_fmt)
lg.addHandler(h)

LOGIN_PAGE = "https://members.iracing.com/membersite/member/results.jsp"
RESULTS_ARCHIVE_PAGE = "https://members.iracing.com/membersite/member/results.jsp"
TEST_XPATH = "/html/body/div[3]/div[2]/div/div/div/div[1]/div[2]/span[3]"


def login(driver):
    # LOGIN_PAGE -> https://members.iracing.com/membersite/member/Home.do
    email = os.getenv("EMAIL")
    password = os.getenv("PASSWORD")

    EMAIL_XPATH = "/html/body/div/div[2]/div/div[2]/form/input[1]"
    PASSWORD_XPATH = "/html/body/div/div[2]/div/div[2]/form/input[2]"
    LOGIN_XPATH = "/html/body/div/div[2]/div/div[2]/form/div/div/div[1]/input"

    url = LOGIN_PAGE
    driver.get(url)

    login_form = driver.find_element(
        by=By.XPATH,
        value=EMAIL_XPATH,
    )
    login_form.send_keys(email)

    password_form = driver.find_element(
        by=By.XPATH,
        value=PASSWORD_XPATH,
    )
    password_form.send_keys(password)

    login_button = driver.find_element(
        by=By.XPATH,
        value=LOGIN_XPATH,
    )
    login_button.click()

    time.sleep(5)

    ## for checking login success
    driver.find_element(by=By.XPATH, value=TEST_XPATH).get_attribute("textContent")
    lg.info("login ok")
    return


# required login
def get_your_subsession_id(driver):
    url = RESULTS_ARCHIVE_PAGE
    driver.get(url)

    time.sleep(5)  # wait for loading RESULTS_ARCHIVE_PAGE
    driver.execute_script("javascript:PageApp.Search(true)")
    time.sleep(5)  # wait for searching

    RESULT_TABLE = "/html/body/table/tbody/tr[6]/td[2]/div/table/tbody/tr[2]/td/div/div[2]/div/div[5]/div[2]/div/div/table"
    result_table = driver.find_element(
        by=By.XPATH,
        value=RESULT_TABLE,
    )

    html = driver.page_source.encode("utf-8")
    print(html)

    soup = BeautifulSoup(html, "html.parser")
    links = soup.find_all("a")
    for link in links:
        print(str(link.get("href")))
    return html


def a_href_list_to_subsession_id(a_href_list):
    subsession_ids = []
    for e in a_href_list:
        if e.find("javascript:launchEventResult(") == -1:
            # not included subsession ID
            continue
        subsession_ids.append(e)
    return subsession_ids
