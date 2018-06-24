import json
import os
import time
import datetime
import threading
from collections import Counter
import re

from fbchat import Client, log
from fbchat.models import Message, ThreadType

import data
from StravaData import checkRunner, getStats, get_weekly_stats

email = os.environ['EMAIL']
password = os.environ['PASSWORD']

class StravaBot(Client):
    all_runners = {}
    current_running_chad = ''
    def pmMe(self, txt):
        self.send(Message(text = txt), thread_id = client.uid, thread_type=ThreadType.USER)

    def onMessage(self, author_id, message_object, thread_id, thread_type, **kwargs):
        if message_object.text is not None:
            messageText = message_object.text
            if re.match("(?i)ghoul", messageText):
                processMessage(self, author_id, messageText, thread_id, thread_type)
            else:
                # Sends the data to the inherited onMessage, so that we can still see when a message is recieved
                super(StravaBot, self).onMessage(author_id=author_id, message_object=message_object, thread_id=thread_id, thread_type=thread_type, **kwargs)



def processMessage(self, author_id, messageText, thread_id, thread_type):
    if author_id != self.uid:
        if re.search("(?i)help", messageText):
            txt = '''
Help for StravaBot:

Precede commands with \'Ghoul\', follow with: commands, [inputs], (options).

ghoul stats [runner]
--Displays year-to-date Strava totals compared to the current chad.

ghoul is [runner] a chad?
--Compares Strava totals of distance, time, and elevation to determine if the runner is the new chad

ghoul add runner [firstname] [stravaId]
--strava id is the set of numbers on your profile page in the form https://www.strava.com/athletes/[stravaId]

ghoul update chad
--will update the current chad and list the current one.

ghoul (get) week
--displays this week's leaderboard from the A0BP strava club. (get) forces update of stats.  

ghoul (get) last week
--displays last week's leaderboard from the A0BP strava club. (get) forces update of stats.
'''
            self.send(Message(text = txt), thread_id = thread_id, thread_type=thread_type)
        elif re.search("(?i)stats",messageText):
            print(messageText)
            iterator = re.finditer(r"(?<=\bstats\s)(\w+)", messageText)
            match = next(iterator)
            runner_name = match[0]
            if match[0] in self.all_runners.keys():
                sendRunningStats(self, thread_id, thread_type, self.all_runners[runner_name], runner_name)
            else:
                self.send(Message(text ='Looks like {} isn\'t in the system. :/'.format(runner_name)), thread_id = thread_id, thread_type=thread_type)
        elif re.search("(?i)is (\w*?) a chad", messageText):
            name = re.findall("is (\w*?) a chad", messageText)[0]
            if name in self.all_runners.keys():
                runningChadCheck(self, thread_id, thread_type, self.all_runners[name], name)
            else:
                self.send(Message(text ='Looks like {} isn\'t in the system. :/'.format(name)), thread_id = thread_id, thread_type=thread_type)

        elif '(?i)add runner' in messageText:
            messageArray = messageText.split(' ')
            runner_name = messageArray[3]
            strava_id = messageArray[4]
            if int(strava_id) in dict(self.all_runners).values():
                self.send(Message(text = '{} already added.'.format(runner_name)), thread_id = thread_id, thread_type=thread_type)
            else:
                print(strava_id)
                print('strava ID ^^^^')
                for value in dict(self.all_runners).values():
                    print(value)
                database_id = checkRunner(runner_name, strava_id)
                if database_id != False:
                    self.all_runners = dict(data.get_runners_list())
                    self.send(Message(text = 'Added {} succesfully, runners list refreshed, id={}'.format(runner_name, database_id)), thread_id = thread_id, thread_type=thread_type)
            getRunners(self, client.uid, ThreadType.USER)
        elif '(?i)update chad' in messageText:
            findChad(self)
            self.send(Message(text = 'Chad updated, running chad is {}'.format(self.current_running_chad)), thread_id = thread_id, thread_type=thread_type)
        # Ghoul get last week (not really intended to be used except for testing and if someone posts a run at 12:01)
        elif re.search("(?i)get last week", messageText):
            self.send(Message(text = print_weekly_leaderboard(data.get_last_weekly_table, True)), thread_id = thread_id, thread_type=thread_type)
        # Ghoul last week
        elif re.search("(?i)last week", messageText):
            self.send(Message(text = print_weekly_leaderboard(data.get_last_weekly_table, False)), thread_id = thread_id, thread_type=thread_type)
        # Ghoul get week
        elif re.search("(?i)get week", messageText):
            self.send(Message(text = print_weekly_leaderboard(data.get_weekly_table, True)), thread_id = thread_id, thread_type=thread_type)
        # Ghoul week
        elif re.search("(?i)week", messageText):
            self.send(Message(text = print_weekly_leaderboard(data.get_weekly_table, False)), thread_id = thread_id, thread_type=thread_type)
        


def sendRunningStats(self, thread_id, thread_type, athlete, athleteName):
    rexStats = getStats(self.all_runners[self.current_running_chad])
    larryStats = getStats(athlete)
    comparedStats = '{} has run {} miles.\n{} has run {} miles.\n\n{} has run for {}:{}.\n{} has run for {}:{}.\n\n{} has climbed {} feet.\n{} has climbed {} feet.\n\n{} has gone for {} runs.\n{} has gone for {} runs.'.format(self.current_running_chad, rexStats[0], athleteName, larryStats[0], self.current_running_chad, rexStats[1], rexStats[2],athleteName, larryStats[1], larryStats[2], self.current_running_chad, rexStats[3],athleteName, larryStats[3], self.current_running_chad, rexStats[4],athleteName, larryStats[4])
    self.send(Message(text = comparedStats), thread_id = thread_id, thread_type=thread_type)

def findChad(self):
    bestTime = [0,'']
    bestDistance = [0.0,'']
    bestElevation = [0,'']
    for runner in self.all_runners:
        runnerStats = getStats(self.all_runners[runner])
        distance = float(runnerStats[0].replace(',',''))
        if distance > bestDistance[0]:
            bestDistance = [distance, runner]
        time = int(runnerStats[1].replace(',',''))
        if time > bestTime[0]:
            bestTime = [time, runner]
        elevation = int(runnerStats[3].replace(',',''))
        if elevation > bestElevation[0]:
            bestElevation = [elevation, runner]
    chadFinalists = Counter([bestTime[1], bestDistance[1], bestElevation[1]])
    print(chadFinalists)
    chadlist = list(chadFinalists.most_common(1))
    print(chadlist)
    if chadlist[0][1] is 1:
        print('CHAD ONLY HAS ONE RECORD, USING DISTANCE TO DETERMINE CHAD.')
        self.current_running_chad = bestDistance[1]
    else:
        print("Chad is {}".format(chadlist[0][0]))
        self.current_running_chad = chadlist[0][0]

def runningChadCheck(self, thread_id, thread_type, athlete, athleteName):
    rexStats = getStats(self.all_runners[self.current_running_chad])
    larryStats = getStats(athlete)
    larryScore = 0
    response = 'I fucked up somehow, whoops'
    if (int(larryStats[1].replace(',','')) > int(rexStats[1].replace(',',''))):
        larryScore = larryScore + 1
    if float(larryStats[0].replace(',','')) > float(rexStats[0].replace(',','')):
        larryScore = larryScore + 1             
    if (int(larryStats[3].replace(',','')) > int(rexStats[3].replace(',',''))):
        larryScore = larryScore + 1
    if larryScore == 3:
        response = 'Yes, {} is currently ahead in {}/3 categories.'.format(athleteName, larryScore)
    else:
        response = 'Not yet, {} is currently ahead in {}/3 categories.'.format(athleteName, larryScore)
    if athleteName == self.current_running_chad:
        response = '{} is the current running chad.'.format(athleteName)

    self.send(Message(text = response), thread_id = thread_id, thread_type=thread_type)

def getRunners(self, thread_id, thread_type):
    runners_list = data.get_runners_list()
    self.all_runners = dict(runners_list)
    print(self.all_runners)
    self.send(Message(text = 'Refreshed runners list.'), thread_id = thread_id, thread_type=thread_type)

def startupClient(email, password): # testing git alias
    try:
        with open("session.txt", "r") as session:
            session_cookies = json.loads(session.read())
    except FileNotFoundError:
        session_cookies = None

    client = StravaBot(email, password, session_cookies=session_cookies)
    with open("session.txt", "w") as session:
        session.write(json.dumps(client.getSession()))
    return client

# Pass in get_[weekly/last_weekly]_table() and whether to run an update first
def print_weekly_leaderboard(desired_table, update):
    leaderboard_elements = desired_table(update)
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
    return weekly_stats_string







### Reving up the engines ###

next_call = time.time()
def update_loop():
    global next_call
    print("Starting timer to next loop: {}".format(datetime.datetime.now()))
    while True:
        try:
            data.update_weekly_table()
            data.update_last_weekly_table()
        except Exception as e:
            print("Selenium failed, retrying, hopefully it works soon :/")
            continue
        break
    next_call = next_call + 60
    threading.Timer(next_call-time.time(), update_loop).start()


client = startupClient(email, password)
getRunners(client, client.uid, ThreadType.USER)
findChad(client)
update_loop()
client.listen()
