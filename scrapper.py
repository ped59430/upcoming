from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from airtable import airtable_download, airtable_upload
import os
import pytz
import re
import datetime
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
# import time
import logging

# Scrapper and Chrome
API_KEY = os.environ['API_KEY']
CHROMEDRIVER_PATH = str(os.environ['CHROMEDRIVER_PATH'])
# GOOGLE_CHROME_PATH = os.environ.get('GOOGLE_CHROME_BIN', “chromedriver”)
chrome_options = Options()
# chrome_options.binary_location = GOOGLE_CHROME_PATH
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-gpu')
# print(CHROMEDRIVER_PATH)
# print(GOOGLE_CHROME_PATH)
# webdriver = Chrome()  # executable_path=CHROMEDRIVER_PATH, options=chrome_options)
# executable_path=CHROMEDRIVER_PATH, options=chrome_options)
webdriver = Chrome(
    executable_path=CHROMEDRIVER_PATH,
    options=chrome_options)


def solve(s):
    return re.sub(r'(\d)(st|nd|rd|th)', r'\1', s)


def scrapper():
    logging.error('begin scrapping')

    # Scrap
    url = 'https://rarity.tools/upcoming/'
    # chrome_driver_path = '/home/runner/Upcoming/chromedriver'

    # get existing records
    airtable_records = airtable_download("Collectibles",
                                         api_key=API_KEY,
                                         base_id="appJtqgtFlRZgvPuV")
    record_dict = {}
    match_field = "Name"
    for record in airtable_records:
        if match_field in record['fields']:
            record_value = record['fields'][match_field]
            record_dict.update({record_value: record['id']})

    with webdriver as driver:
        # Set timeout time
        wait = WebDriverWait(driver, 10)

        # retrive url in headless browser
        driver.get(url)
        wait.until(presence_of_element_located((By.TAG_NAME, "table")))

        # find table
        table = driver.find_element_by_tag_name("table")

        # get rows
        # rows = table.find_elements_by_tag_name("tr")
        rows = table.find_elements_by_xpath(
            "//tr[contains(@class, 'text-gray-800') and not(contains(@class, 'featuredUpcoming'))]"
        )

        # get values in rows
        for row in rows:
            upload_data = {}
            cells = row.find_elements_by_tag_name("td")
            if len(cells) >= 4:
                cell_0 = cells[0].find_elements_by_tag_name("div")
                # Overview
                upload_data["Name"] = cell_0[0].text
                logging.error(upload_data["Name"])
                upload_data["Description"] = cell_0[1].text
                try:
                    upload_data["Image"] = cells[0].find_element_by_xpath(
                        ".//img[contains(@src, 'imagekit')]"
                    ).get_attribute('src')
                except NoSuchElementException:
                    pass
                # Links
                try:
                    upload_data["Discord"] = cells[
                        1].find_element_by_xpath(
                            ".//a[contains(@href, 'discord')]"
                    ).get_attribute('href')
                except NoSuchElementException:
                    pass
                try:
                    upload_data["Twitter"] = cells[
                        1].find_element_by_xpath(
                            ".//a[contains(@href, 'twitter')]"
                    ).get_attribute('href')
                except NoSuchElementException:
                    pass
                cell_1 = cells[1].find_elements_by_tag_name("a")
                if len(cell_1) >= 3:
                    upload_data["Website"] = cell_1[2].get_attribute(
                        'href')
                else:
                    upload_data["Website"] = ""
                # Minting
                cell_2 = cells[2].find_elements_by_tag_name("div")
                if len(cell_2) == 1:
                    upload_data["Supply"] = cell_2[0].text
                elif len(cell_2) == 2:
                    upload_data["Supply"] = cell_2[1].text
                try:
                    upload_data["Pricing"] = cells[2].find_element_by_xpath(
                        ".//div[contains(@class, 'text-green-500')]").text
                except NoSuchElementException:
                    pass
                cell_3 = cells[3].text.split("\n")
                if len(cell_3) == 3:
                    p = re.compile('\((.*?)\)')
                    date_timezone = p.findall(cell_3[2])[0]
                    date_value = cell_3[2].rstrip(" (" + date_timezone +
                                                  ")")
                    date_time_str = cell_3[1].split(
                        ", ")[1] + " " + date_value
                    sale_date = datetime.datetime.strptime(
                        solve(date_time_str), '%B %d %Y %I:%M %p')
                    timezone = pytz.timezone(date_timezone)
                    timezone_date_time_obj = timezone.localize(sale_date)
                    upload_data[
                        "Sale date"] = timezone_date_time_obj.isoformat()
            # find if matching
            match_value = upload_data["Name"]
            record_id = record_dict.get(match_value)
            airtable_upload("Collectibles",
                            upload_data,
                            api_key=API_KEY,
                            base_id="appJtqgtFlRZgvPuV",
                            record_id=record_id)

        # must close the driver after task finished
        driver.close()
    logging.error("Done")
    logging.error("Waiting for one day")
    # time.sleep(86400)


if __name__ == '__main__':
    print('main')
    scrapper()
