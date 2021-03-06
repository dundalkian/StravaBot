from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from bs4 import BeautifulSoup
import urllib3
import data
import re
import os
import time 
## Config ##
club_url="https://www.strava.com/clubs/A0BP"
## ##

def get_weekly_stats():
    chrome_options = Options()
    chrome_options.binary_location = os.environ['GOOGLE_CHROME_BIN']
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(executable_path=os.environ['CHROMEDRIVER_PATH'], chrome_options=chrome_options)
    driver.get(club_url)
    leaderboard = driver.find_element_by_css_selector("body > div.view > div.page.container > div:nth-child(4) > div.spans11 > div.leaderboard-page.tab-content > div:nth-child(2) > div.leaderboard > table")
    leaderboard_elements = []
    for row in leaderboard.find_elements_by_tag_name("tr"):
        leaderboard_elements.append(re.split('(?<=\D)\s+(?=\d)|(?<=\d)\s+(?=\d)|\\n', row.text))
    # Header information of table, will also throw an error if no table exists
    try:
        leaderboard_elements.pop(0)
    except IndexError as e:
        print("Error reading table: {}".format(e))
        return False
    # [Rank, Athlete, Distance, Runs, Longest, Avg. Pace, Elev. Gain] for reference
    driver.quit()
    return leaderboard_elements

def get_last_weekly_stats():
    chrome_options = Options()
    chrome_options.binary_location = os.environ['GOOGLE_CHROME_BIN']
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(executable_path=os.environ['CHROMEDRIVER_PATH'], chrome_options=chrome_options)

    # This banner is in the way of clicking the last week button and idk how to scroll
    cookie_button_selector = "#stravaCookieBanner > div > button"
    selector = "body > div.view > div.page.container > div:nth-child(4) > div.spans11 > div.leaderboard-page.tab-content > div:nth-child(2) > ul > li:nth-child(1) > span" 
    driver.maximize_window()
    driver.get(club_url)
    cookie_button = driver.find_element_by_css_selector(cookie_button_selector)
    cookie_button.click()
    button = driver.find_element_by_css_selector(selector)
    button.click()
    
    leaderboard = driver.find_element_by_css_selector("body > div.view > div.page.container > div:nth-child(4) > div.spans11 > div.leaderboard-page.tab-content > div:nth-child(2) > div.leaderboard > table")
    leaderboard_elements = []
    for row in leaderboard.find_elements_by_tag_name("tr"):
        leaderboard_elements.append(re.split('(?<=\D)\s+(?=\d)|(?<=\d)\s+(?=\d)|(?<=m) (?=--)|\\n', row.text))
    # Header information of table, will also throw an error if no table exists
    leaderboard_elements.pop(0) 
    # [Rank, Athlete, Distance, Runs, Longest, Avg. Pace, Elev. Gain] for reference
    driver.quit()
    return leaderboard_elements

"""
weekly_stats_string = ""
    km_2_mi = 0.621371
    club_total_distance = 0.0
    for element in leaderboard_elements:
        distance_str = element[2].split(' ')
        miles = float(distance_str[0])*km_2_mi
        distance_str = "{:.1f} mi".format(miles)
        club_total_distance += miles
        weekly_stats_string += "{}: {}\n".format(element[1],distance_str)

    weekly_stats_string += "\nClub Miles: {:.1f} mi".format(club_total_distance)
"""





#get_last_weekly_stats()



# At this point I hate HTML a lot, so it works for now, not worth to fix.
def getStats(Id):
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
    print(final)
    Distance = final[1][1:-1] + ' mi '
    Time = final[4][1:-1] + ':' + final[6][2:-1] + ' '
    Elevation = final[9][1:-1] +  ' ft '
    Runs = final[12][1:-1]

    print(Distance + Time + Elevation + Runs)
    return [final[1][1:-1], final[4][1:-1], final[6][2:-1], final[9][1:-1], final[12][1:-1]]


def checkRunner(nameToCheck, idToCheck):
    url = "https://www.strava.com/athletes/" + str(idToCheck)
    http_pool = urllib3.connection_from_url(url)
    r = http_pool.urlopen('GET',url)

    soup = BeautifulSoup(r.data.decode('utf-8'), 'html.parser')

    athlete = soup.find(class_='bottomless').string
    if nameToCheck in athlete.lower():
        database_id = data.insert_runner(nameToCheck, idToCheck)
        if database_id:
            return database_id
        else:
            return False
    else:
        return False
