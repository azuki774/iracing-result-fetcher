import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import logging
from pythonjsonlogger import jsonlogger
import iracing


lg = logging.getLogger(__name__)
lg.setLevel(logging.DEBUG)
h = logging.StreamHandler()
h.setLevel(logging.DEBUG)
json_fmt = jsonlogger.JsonFormatter(
    fmt="%(asctime)s %(levelname)s %(name)s %(message)s", json_ensure_ascii=False
)
h.setFormatter(json_fmt)
lg.addHandler(h)


def get_driver():
    driver = webdriver.Remote(
        command_executor="http://selenium:4444/wd/hub",
        options=webdriver.ChromeOptions(),
    )
    return driver


def main():
    lg.info("fetcher start")
    lg.info("wait sleep for starting server")
    time.sleep(int(os.getenv("START_SLEEP", default="0")))
    lg.info("Get driver")
    driver = get_driver()
    driver.implicitly_wait(10)
    iracing.login(driver)
    subsession_ids = iracing.get_your_subsession_id(driver)
    for s in subsession_ids:
        iracing.proc_result_record(driver, s)


if __name__ == "__main__":
    main()
