import json
import os
import time
from collections import Counter

from fbchat import Client, log
from fbchat.models import *

import data
from StravaData import checkRunner, getStats

email = os.environ['EMAIL']
password = os.environ['PASSWORD']

class StravaBot(Client):
    all_runners = {}
    all_lifters = []
    current_running_chad = ''
    current_lifting_chad = ''
    def pmMe(self, txt):
        self.send(Message(text = txt), thread_id = client.uid, thread_type=ThreadType.USER)

    def onMessage(self, author_id, message_object, thread_id, thread_type, **kwargs):
        if message_object.text is not None:
            messageText = message_object.text.lower()
            if 'ghoul' in messageText: 
                processMessage(self, author_id, messageText, thread_id, thread_type)
            else:
                # Sends the data to the inherited onMessage, so that we can still see when a message is recieved
                super(StravaBot, self).onMessage(author_id=author_id, message_object=message_object, thread_id=thread_id, thread_type=thread_type, **kwargs)



def processMessage(self, author_id, messageText, thread_id, thread_type):
    if author_id != self.uid:
        if 'help' in messageText:
            txt = '''
Help for StravaBot:

Precede commands with \'Ghoul\', follow with desired command and [inputs].

ghoul stats [runner] --Displays year-to-date Strava totals compared to the current chad.

ghoul is [runner] a chad? --Compares Strava totals of distance, time, and elevation to determine if the runner is the new chad

ghoul add lift [athlete] [lift type] [lift weight] --Adds one lift to the db

ghoul get lift pr [athlete] [lift type] --Finds your pr for the specified lift type

ghoul add runner [firstname] [stravaId]
strava id is the set of numbers on your profile page in the form https://www.strava.com/athletes/[stravaId]

ghoul update chad 
will update the current chad and list the current one
'''
            self.send(Message(text = txt), thread_id = thread_id, thread_type=thread_type)
        elif 'stats' in messageText:
            messageArray = messageText.split(' ')
            runner_name = messageArray[2]
            if runner_name in self.all_runners.keys():
                sendRunningStats(self, thread_id, thread_type, self.all_runners[runner_name], runner_name)
            else:
                self.send(Message(text ='Looks like {} isn\'t in the system. :/'.format(runner_name)), thread_id = thread_id, thread_type=thread_type)
        elif ('is' and 'a chad') in messageText:
            messageArray = messageText.split(' ')
            name = messageArray[2]
            lifter = False
            runner = False
            if name in self.all_runners.keys():
                runner = True
                runningChadCheck(self, thread_id, thread_type, self.all_runners[name], name)
            if name in self.all_lifters.keys():
                lifter = True
                liftingChadCheck(self, thread_id, thread_type, self.all_lifters[name], name)
            if (not runner and not lifter):
                self.send(Message(text ='Looks like {} isn\'t in either system. :/'.format(name)), thread_id = thread_id, thread_type=thread_type)
                
            # elif 'is kuoyuan a chad' in messageText:
            #         athleteName = 'Kuoyuan'
            #         chadCheck(self, thread_id, thread_type, Kuoyuan, athleteName)
        elif 'lift report' in messageText:
            FB_user_dict = StravaBot.fetchUserInfo(self, author_id)
            FB_user = list(FB_user_dict.values())[0]
            FB_user_name = FB_user.first_name.lower()
            print('user\'s name is' + FB_user_name)
            if FB_user_name not in self.all_lifters:
                self.all_lifters.append(FB_user_name)

            messageArray = messageText.split(' ')
            num_of_lifts = 0
            majorLifts = ['squat', 'dl', 'row', 'bench', 'ohp']
            for lift in majorLifts:
                if lift in messageArray:
                    index = messageArray.index(lift)
                    lift_name = lift
                    lift_weight = messageArray[index+1]
                    lift_id = data.insert_lift(FB_user_name, lift_name, lift_weight)
                    num_of_lifts += 1
            if num_of_lifts > 0:
                self.send(Message(text = 'Nice gains brah.'), thread_id = thread_id, thread_type=thread_type)
            else:
                self.send(Message(text = 'Bro do you even lift?'), thread_id = thread_id, thread_type=thread_type)
        elif 'add lift' in messageText:
            messageArray = messageText.split(' ')
            athlete_name = messageArray[3]
            lift_name = messageArray[4]
            lift_weight = messageArray[5]
            lift_id = data.insert_lift(athlete_name, lift_name, lift_weight)
            self.send(Message(text = 'This is the lift id: ' + str(lift_id) + ', if there is nothing there something fucked up.'), thread_id = thread_id, thread_type=thread_type)
        elif 'get lift pr' in messageText:
            messageArray = messageText.split(' ')
            athlete_name = messageArray[4]
            lift_name = messageArray[5]
            pr = data.get_lift_pr(athlete_name, lift_name)
            self.send(Message(text = 'This is your pr: ' + str(pr)), thread_id = thread_id, thread_type=thread_type)
        elif 'add runner' in messageText:
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
        elif 'update chad' in messageText:
            findChad(self)
            self.send(Message(text = 'Chad updated, running chad is {}'.format(self.current_running_chad)), thread_id = thread_id, thread_type=thread_type)
            

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

def liftingChadCheck(self, thread_id, thread_type, athlete, athleteName):
    chadStats = data.get_lift_stats(self.current_lifting_chad)
    virginStats = data.get_lift_stats(athleteName)
    virginScore = 0
    response = 'I fucked up somehow, whoops'
    if virginStats[0] > chadStats[0]:
        virginScore = virginScore + 1
    if virginStats[1] > chadStats[1]:
        virginScore = virginScore + 1
    if virginStats[2] > chadStats[2]:
        virginScore = virginScore + 1
    if virginStats[3] > chadStats[3]:
        virginScore = virginScore + 1
    if virginStats[4] > chadStats[4]:
        virginScore = virginScore + 1
    if virginScore == 5:
        response = 'Yes, {} is currently ahead in {}/5 lifts.'.format(athleteName, virginScore)
    else:
        response = 'Not yet, {} is currently ahead in {}/5 lifts.'.format(athleteName, virginScore)
    if athleteName == self.current_lifting_chad:
        response = '{} is the current lifting chad.'.format(athleteName)

    self.send(Message(text = response), thread_id = thread_id, thread_type=thread_type)

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
   

def startupClient(email, password):
    try:
        with open("session.txt", "r") as session:
            session_cookies = json.loads(session.read())
    except FileNotFoundError:
        session_cookies = None

    client = StravaBot(email, password, session_cookies=session_cookies)
    with open("session.txt", "w") as session:
        session.write(json.dumps(client.getSession()))
    return client



client = startupClient(email, password)
getRunners(client, client.uid, ThreadType.USER)
findChad(client)
client.listen()
