import os
import re
import time

import urllib3
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

# Project imports
import data_handler

## Config ##
club_url="https://www.strava.com/clubs/A0BP"
## ##

def scrape_club_table(last_week=False):
    chrome_options = Options()
    chrome_options.binary_location = os.environ['GOOGLE_CHROME_BIN']
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(executable_path=os.environ['CHROMEDRIVER_PATH'], chrome_options=chrome_options)
    driver.get(club_url)

    if last_week:
        # This banner is in the way of clicking the last week button and idk how to scroll
        cookie_button_selector = "#stravaCookieBanner > div > button"
        last_week_button_selector = "body > div.view > div.page.container > div:nth-child(4) > div.spans11 > div.leaderboard-page.tab-content > div:nth-child(2) > ul > li:nth-child(1) > span" 
        driver.maximize_window()
        # Find the cookie banner close button and click it
        cookie_button = driver.find_element_by_css_selector(cookie_button_selector)
        cookie_button.click()
        # Find the last week button and click it
        button = driver.find_element_by_css_selector(last_week_button_selector)
        button.click()    
    
    leaderboard = driver.find_element_by_css_selector("body > div.view > div.page.container > div:nth-child(4) > div.spans11 > div.leaderboard-page.tab-content > div:nth-child(2) > div.leaderboard > table")
    driver.quit()
    return leaderboard.find_elemens_by_tag_name("tr")

# At this point I hate HTML a lot, so it works for now, not worth to fix.
def get_stats(Id):
    url = "https://www.strava.com/athletes/" + str(Id)
    http_pool = urllib3.connection_from_url(url)
    r = http_pool.urlopen('GET',url)
    soup = BeautifulSoup(r.data.decode('utf-8'), 'html.parser')
    table = soup.table
    t = []
    for child in table.children:
        t.append(child)
    tbody = t[3]
    tr = []
    for child in tbody.children:
        if child != '\n':
            tr.append(child)
    final = []
    for r in tr:
        for string in r.strings:
            if string != '\n':
                final.append(repr(string))
    # Left for reference, was previously printed as reference. _indices_ :/
    #Distance = final[1][1:-1] + ' mi '
    #Time = final[4][1:-1] + ':' + final[6][2:-1] + ' '
    #Elevation = final[9][1:-1] +  ' ft '
    #Runs = final[12][1:-1]

    return [final[1][1:-1], final[4][1:-1], final[6][2:-1], final[9][1:-1], final[12][1:-1]]


def check_runner(name_to_check, id_to_check):
    url = "https://www.strava.com/athletes/" + str(id_to_check)
    http_pool = urllib3.connection_from_url(url)
    r = http_pool.urlopen('GET',url)

    soup = BeautifulSoup(r.data.decode('utf-8'), 'html.parser')


    athlete = soup.find(class_='bottomless').string

    if name_to_check in athlete.lower():
        database_id = data_handler.add_runner(name_to_check, id_to_check)
        if database_id:
            return database_id
        else:
            return False
    else:
        return False
