import urllib3
from bs4 import BeautifulSoup
import data


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
