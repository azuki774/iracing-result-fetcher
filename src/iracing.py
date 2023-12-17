import json
import csv
import time
import datetime as dt
import os
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
import re
from pythonjsonlogger import jsonlogger

FETCH_WAIT_TIME = 7

lg = logging.getLogger(__name__)
lg.setLevel(logging.DEBUG)
h = logging.StreamHandler()
h.setLevel(logging.DEBUG)
json_fmt = jsonlogger.JsonFormatter(
    fmt="%(asctime)s %(levelname)s %(name)s %(message)s", json_ensure_ascii=False
)
h.setFormatter(json_fmt)
lg.addHandler(h)

DATA_BASEDIR = "/data"

LOGIN_PAGE = "https://members.iracing.com/membersite/member/results.jsp"
RESULTS_ARCHIVE_PAGE = "https://members.iracing.com/membersite/member/results.jsp"
TEST_XPATH = "/html/body/div[3]/div[2]/div/div/div/div[1]/div[2]/span[3]"
RESULT_CSV_BASE = "https://members.iracing.com/membersite/member/EventResult.do"


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

    time.sleep(FETCH_WAIT_TIME)

    ## for checking login success
    driver.find_element(by=By.XPATH, value=TEST_XPATH).get_attribute("textContent")
    lg.info("login ok")
    return


# required login
def get_your_subsession_id(driver):
    subsession_ids = []
    url = RESULTS_ARCHIVE_PAGE
    driver.get(url)

    time.sleep(FETCH_WAIT_TIME)  # wait for loading RESULTS_ARCHIVE_PAGE

    # Season select
    choose_season(driver)
    lg.info("year: {}, season: {}".format(os.getenv("YEAR"), os.getenv("SEASON")))

    driver.execute_script("javascript:PageApp.Search(true)")  # press search button
    lg.info("press Search button")
    time.sleep(FETCH_WAIT_TIME)  # wait for searching

    # one page or two pages in this condition?
    try:
        # Get the number of Pages
        SELECTOR = driver.find_element(
            by=By.XPATH,
            value="/html/body/table/tbody/tr[6]/td[2]/div/table/tbody/tr[2]/td/div/div[2]/div/div[4]/p/select",
        )
        select = Select(SELECTOR)
        all_options = select.options
        page_num = len(all_options)
    except:
        # no page SELECTOR (maybe one page)
        lg.info("no SELECTOR found")
        page_num = 1

    lg.info("detected {} pages".format(page_num))

    for i in range(page_num):
        # one page process
        lg.info("fetching {}/{}".format(i + 1, page_num))
        time.sleep(FETCH_WAIT_TIME)  # wait for searching

        RESULT_TABLE = "/html/body/table/tbody/tr[6]/td[2]/div/table/tbody/tr[2]/td/div/div[2]/div/div[5]/div[2]/div/div/table"
        result_table = driver.find_element(
            by=By.XPATH,
            value=RESULT_TABLE,
        )

        html = driver.page_source.encode("utf-8")

        soup = BeautifulSoup(html, "html.parser")
        links = soup.find_all("a")
        a_href_list = []
        for link in links:
            a_href_list.append(str(link.get("href")))

        subsession_ids = subsession_ids + a_href_list_to_subsession_id(a_href_list)

        if i + 1 == page_num:  # if last page
            break

        # next page
        driver.execute_script("javascript:PageApp.UI.PageForward()")
        time.sleep(FETCH_WAIT_TIME)  # wait for searching

    return subsession_ids


def choose_season(driver):
    YEAR_XPATH = "/html/body/table/tbody/tr[6]/td[2]/div/table/tbody/tr[2]/td/div/div[2]/div/div[2]/div[2]/select[1]"
    SEASON_XPATH = "/html/body/table/tbody/tr[6]/td[2]/div/table/tbody/tr[2]/td/div/div[2]/div/div[2]/div[2]/select[2]"
    year_selector = driver.find_element(
        by=By.XPATH,
        value=YEAR_XPATH,
    )
    season_selector = driver.find_element(
        by=By.XPATH,
        value=SEASON_XPATH,
    )

    year = os.getenv("YEAR")
    season = os.getenv("SEASON")
    select_year = Select(year_selector)
    select_season = Select(season_selector)

    if year is not None:
        select_year.select_by_value(year)

    if season is not None:
        select_season.select_by_value(season)

    # environment varible overwrited
    os.environ["YEAR"] = select_year.first_selected_option.get_attribute("value")
    os.environ["SEASON"] = select_season.first_selected_option.get_attribute("value")
    time.sleep(FETCH_WAIT_TIME)
    return year, season


def a_href_list_to_subsession_id(a_href_list):
    subsession_ids = []
    for e in a_href_list:
        if e.find("javascript:launchEventResult(") == -1:
            # not included subsession ID
            continue
        subsession_id = re.findall("[0-9]+", e)[0]
        subsession_ids.append(subsession_id)

    return subsession_ids


def proc_result_record(driver, subsession_id):
    year = os.getenv("YEAR")
    season = os.getenv("SEASON")
    DATA_DIR = DATA_BASEDIR + "/" + year + "/" + season
    os.makedirs(DATA_DIR, exist_ok=True)

    META_FILE_PATH = DATA_DIR + "/{}_meta.json".format(subsession_id)
    if os.path.isfile(META_FILE_PATH):
        lg.info("already existed. skipping download: {}".format(META_FILE_PATH))
        return
    record = download_result_record(driver, subsession_id)
    write_meta_data(record, META_FILE_PATH)
    lg.info("write meta data: {}".format(META_FILE_PATH))

    RESULT_FILE_PATH = DATA_DIR + "/{}_result.csv".format(subsession_id)
    write_result_data(record["result"], RESULT_FILE_PATH)
    lg.info("write result data: {}".format(RESULT_FILE_PATH))
    return


def download_result_record(driver, subsession_id):
    params = "?subsessionid={0}".format(subsession_id)
    url = RESULT_CSV_BASE + params
    driver.get(url)
    lg.info("get data: {0}".format(url))
    time.sleep(FETCH_WAIT_TIME)  # wait for loading
    soup = BeautifulSoup(driver.page_source, "html.parser")
    race_table = soup.find_all("table", class_="event_table")[1]
    m = []
    tbody = race_table.find("tbody")
    trs = tbody.find_all("tr")
    for tr in trs:
        r = []
        for td in tr.find_all("td"):
            r.append(td.text)
        m.append(r)
    ms = m[4:][0::2]  # ignore header and empty data & skip duplicate data

    record = {}
    record["result"] = ms

    SEASON_TABLE = "/html/body/div/div/div/div/table/tbody/tr/td[2]/div[1]"
    record["season"] = driver.find_element(
        by=By.XPATH,
        value=SEASON_TABLE,
    ).get_attribute("textContent")

    DATETIME_TABLE = "/html/body/div/div/div/div/table/tbody/tr/td[2]/div[2]"
    record["datetime"] = driver.find_element(
        by=By.XPATH,
        value=DATETIME_TABLE,
    ).get_attribute("textContent")

    TRACK_NAME_TABLE = "/html/body/div/div/div/div/table/tbody/tr/td[2]/div[3]"
    record["track_name"] = driver.find_element(
        by=By.XPATH,
        value=TRACK_NAME_TABLE,
    ).get_attribute("textContent")

    SESSON_ID_TABLE = "/html/body/div/div/div/div/table/tbody/tr/td[2]/div[4]"
    record["sesson_id"] = driver.find_element(
        by=By.XPATH,
        value=SESSON_ID_TABLE,
    ).get_attribute("textContent")

    SESSON_AVERAGE_LAP_TABLE = (
        "/html/body/div/div/div/div/div[2]/table/tbody/tr[3]/td[1]"
    )
    record["average_lap"] = driver.find_element(
        by=By.XPATH,
        value=SESSON_AVERAGE_LAP_TABLE,
    ).get_attribute("textContent")

    LAP_COMPLETED_TABLE = "/html/body/div/div/div/div/div[2]/table/tbody/tr[3]/td[2]"
    record["lap_completed"] = driver.find_element(
        by=By.XPATH,
        value=LAP_COMPLETED_TABLE,
    ).get_attribute("textContent")

    CAUTIONS_TABLE = "/html/body/div/div/div/div/div[2]/table/tbody/tr[3]/td[3]"
    record["cautions"] = driver.find_element(
        by=By.XPATH,
        value=CAUTIONS_TABLE,
    ).get_attribute("textContent")

    CAUTIONS_LAP_TABLE = "/html/body/div/div/div/div/div[2]/table/tbody/tr[3]/td[4]"
    record["cautions_lap"] = driver.find_element(
        by=By.XPATH,
        value=CAUTIONS_LAP_TABLE,
    ).get_attribute("textContent")

    LEAD_CHANGE_TABLE = "/html/body/div/div/div/div/div[2]/table/tbody/tr[3]/td[5]"
    record["lead_change"] = driver.find_element(
        by=By.XPATH,
        value=LEAD_CHANGE_TABLE,
    ).get_attribute("textContent")

    SOF_TABLE = "/html/body/div/div/div/div/div[2]/table/tbody/tr[3]/td[6]"
    record["sof"] = driver.find_element(
        by=By.XPATH,
        value=SOF_TABLE,
    ).get_attribute("textContent")
    return record


def write_meta_data(record, savedir):
    with open(savedir, mode="w") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)
    return


def write_result_data(result, savedir):
    # Pos
    # Class Pos
    # Car
    # Class,
    # Car #
    # Driver
    # Start Pos
    # Out
    # Interval
    # Laps Led
    # Average Lap Time
    # Fastest Lap Time
    # Fast Lap#
    # Laps Comp
    # Inc
    # Champ
    # Pts
    # Gross Club Pts
    # Div
    # Club
    # iRating
    # License
    # License Rating
    # License Moving
    header = "Pos,ClassPos,Car,Class,Car #,Driver,StartPos,Out,Interval,LapsLed,AverageLapTime,FastestLapTime,FastLap,LapsComp,Inc,Champ,Pts,GrossClubPts,Div,Club,iRating,License,LicenseRating,LicenseMoving"
    with open(savedir, mode="w") as f:
        f.write(header + "\n")
        writer = csv.writer(f, lineterminator="\n")
        writer.writerows(result)

    return
