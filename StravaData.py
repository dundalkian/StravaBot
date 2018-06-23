from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
import urllib3
import data
import re
import os
import time 
## Config ##
club_url="https://www.strava.com/clubs/A0BP"
## ##

# executable_path=os.environ['CHROMEDRIVER_PATH'], 
def get_weekly_stats():
    chrome_options = Options()
    #chrome_options.binary_location = os.environ['GOOGLE_CHROME_BIN']
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(chrome_options=chrome_options)
    driver.get(club_url)
    leaderboard = driver.find_element_by_xpath("//table[@class='dense striped sortable']")
    leaderboard_elements = []
    for row in leaderboard.find_elements_by_tag_name("tr"):
        leaderboard_elements.append(re.split('(?<=\D)\s+(?=\d)|(?<=\d)\s+(?=\d)|\\n', row.text))
    # Header information of table, will also throw an error if no table exists
    leaderboard_elements.pop(0) 
    # [Rank, Athlete, Distance, Runs, Longest, Avg. Pace, Elev. Gain] for reference
    driver.quit()
    return leaderboard_elements

def get_last_weekly_stats():
    chrome_options = Options()
    #chrome_options.binary_location = os.environ['GOOGLE_CHROME_BIN']
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(chrome_options=chrome_options)
    driver.get(club_url) 
    path = "/html/body/div[2]/div[2]/div[4]/div[1]/div[2]/div[2]/ul/li[1]/span"
    button = driver.find_element_by_xpath(path)
    actions = ActionChains(driver)
    actions.move_to_element(button)
    actions.click(button)
    actions.perform()
    actions.pause(5)
    leaderboard = driver.find_element_by_xpath("//table[@class='dense striped sortable']")
    leaderboard_elements = []
    for row in leaderboard.find_elements_by_tag_name("tr"):
        leaderboard_elements.append(re.split('(?<=\D)\s+(?=\d)|(?<=\d)\s+(?=\d)|\\n', row.text))
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





#print(get_last_weekly_stats())



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
