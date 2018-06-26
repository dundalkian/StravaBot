import re
from collections import Counter

from fbchat.models import Message, ThreadType

import scraper
import bot
import database

help_text = '''
Help for StravaBot:
Precede commands with \'Ghoul\', follow with: commands, [inputs], (options).

## ghoul stats [runner]
displays year-to-date Strava totals compared to the current chad.
## ghoul is [runner] a chad?
Compares Strava totals of distance, time, and elevation to determine if the runner is the new chad
## ghoul add runner [firstname] [stravaId]
strava id is the set of numbers on your profile page in the form https://www.strava.com/athletes/[stravaId]
## ghoul update chad
will update the current chad and list the current one.
## ghoul (get) week
displays this week's leaderboard from the A0BP strava club. (get) forces update of stats.  
## ghoul (get) last week
displays last week's leaderboard from the A0BP strava club. (get) forces update of stats.
'''
####################################################
### Top section is mainly for message processing ###
####################################################
def process_message(StravaBot, author_id, messageText, thread_id, thread_type):
    if author_id != StravaBot.uid:
        if re.search("(?i)help", messageText):
            StravaBot.send(Message(text = help_text), thread_id = thread_id, thread_type=thread_type)
        elif re.search("(?i)stats",messageText):
            print(messageText)
            iterator = re.finditer(r"(?<=\bstats\s)(\w+)", messageText)
            match = next(iterator)
            runner_name = match[0]
            if match[0] in StravaBot.all_runners.keys():
                sendRunningStats(StravaBot, thread_id, thread_type, StravaBot.all_runners[runner_name], runner_name)
            else:
                return 'Looks like {} isn\'t in the system. :/'.format(runner_name)
        elif re.search("(?i)is (\w*?) a chad", messageText):
            name = re.findall("is (\w*?) a chad", messageText)[0]
            if name in StravaBot.all_runners.keys():
                return runningChadCheck(StravaBot, StravaBot.all_runners[name], name)
            else:
                return 'Looks like {} isn\'t in the system. :/'.format(name)

        elif '(?i)add runner' in messageText:
            messageArray = messageText.split(' ')
            runner_name = messageArray[3]
            strava_id = messageArray[4]
            if int(strava_id) in dict(StravaBot.all_runners).values():
                return '{} already added.'.format(runner_name)
            else:
                print(strava_id)
                print('strava ID ^^^^')
                for value in dict(StravaBot.all_runners).values():
                    print(value)
                database_id = database.insert_runner(runner_name, strava_id)
                if database_id != False:
                    StravaBot.all_runners = dict(database.get_runners_list())
                    return 'Added {} succesfully, runners list refreshed, id={}'.format(runner_name, database_id)
        elif '(?i)update chad' in messageText:
            findChad(StravaBot)
            return 'Chad updated, running chad is {}'.format(StravaBot.current_running_chad)
        # Ghoul get last week (not really intended to be used except for testing and if someone posts a run at 12:01)
        elif re.search("(?i)get last week", messageText):
            return get_ranking_name_and_distance(True, True)
        # Ghoul last week
        elif re.search("(?i)last week", messageText):
            return get_ranking_name_and_distance(False, True)
        # Ghoul get week
        elif re.search("(?i)get week", messageText):
            return get_ranking_name_and_distance(True, False)
        # Ghoul week
        elif re.search("(?i)week", messageText):
            return get_ranking_name_and_distance(False, False)

def sendRunningStats(StravaBot, thread_id, thread_type, athlete, athlete_name):
    rex_stats = get_individual_stats(StravaBot.all_runners[StravaBot.current_running_chad])
    larry_stats = get_individual_stats(athlete)
    compared_stats = '{} has run {} miles.\n{} has run {} miles.\n\n{} has run for {}:{}.\n{} has run for {}:{}.\n\n{} has climbed {} feet.\n{} has climbed {} feet.\n\n{} has gone for {} runs.\n{} has gone for {} runs.'.format(StravaBot.current_running_chad, rex_stats[0], athlete_name, larry_stats[0], StravaBot.current_running_chad, rex_stats[1], rex_stats[2],athlete_name, larry_stats[1], larry_stats[2], StravaBot.current_running_chad, rex_stats[3],athlete_name, larry_stats[3], StravaBot.current_running_chad, rex_stats[4],athlete_name, larry_stats[4])
    return compared_stats

def findChad(StravaBot):
    bestTime = [0,'']
    bestDistance = [0.0,'']
    bestElevation = [0,'']
    for runner in StravaBot.all_runners:
        runnerStats = get_individual_stats(StravaBot.all_runners[runner])
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
        StravaBot.current_running_chad = bestDistance[1]
    else:
        print("Chad is {}".format(chadlist[0][0]))
        StravaBot.current_running_chad = chadlist[0][0]

def runningChadCheck(StravaBot, athlete, athlete_name):
    rex_stats = get_individual_stats(StravaBot.all_runners[StravaBot.current_running_chad])
    larry_stats = get_individual_stats(athlete)
    larryScore = 0
    response = 'I fucked up somehow, whoops'
    if (int(larry_stats[1].replace(',','')) > int(rex_stats[1].replace(',',''))):
        larryScore = larryScore + 1
    if float(larry_stats[0].replace(',','')) > float(rex_stats[0].replace(',','')):
        larryScore = larryScore + 1             
    if (int(larry_stats[3].replace(',','')) > int(rex_stats[3].replace(',',''))):
        larryScore = larryScore + 1
    if larryScore == 3:
        response = 'Yes, {} is currently ahead in {}/3 categories.'.format(athlete_name, larryScore)
    else:
        response = 'Not yet, {} is currently ahead in {}/3 categories.'.format(athlete_name, larryScore)
    if athlete_name == StravaBot.current_running_chad:
        response = '{} is the current running chad.'.format(athlete_name)
    return response

def getRunners(StravaBot, thread_id, thread_type):
    runners_list = get_runners_list()
    StravaBot.all_runners = dict(runners_list)
    print(StravaBot.all_runners)
    StravaBot.send(Message(text = 'Refreshed runners list.'), thread_id = thread_id, thread_type=thread_type)

#################################################
### Following lean more towards data handling ###
#################################################
def get_ranking_name_and_distance(update=False, last_week=False):
    """ This will give ranking by distance for the desired week as a string"""
    table = database.get_db_table(update, last_week)
    weekly_stats_string = ""
    km_2_mi = 0.621371
    club_total_distance = 0.0
    for runner_stats in table:
        distance_str = runner_stats[2].split(' ')
        miles = float(distance_str[0])*km_2_mi
        distance_str = "{:.1f} mi".format(miles)
        club_total_distance += miles
        weekly_stats_string += "{}: {}\n".format(runner_stats[1],distance_str)


    weekly_stats_string += "\nClub Miles: {:.1f} mi".format(club_total_distance)
    return weekly_stats_string

def update_tables():
    database.update_db_club_table(last_week=True)
    database.update_db_club_table(last_week=False)
    return

# Takes in a list of 'tr' elements from the scraper module
# and splits/organizes them into a standardized list
def parse_elements_from_table(last_week=False):
    table_rows = scraper.scrape_club_table(last_week)
    leaderboard_elements=[]
    for row in table_rows:
        leaderboard_elements.append(re.split('(?<=\D)\s+(?=\d)|(?<=\d)\s+(?=\d)|\\n', row.text))
     # Remove header information of table, will also throw an error if no table exists
    leaderboard_elements.pop(0) 
    # [Rank, Athlete, Distance, Runs, Longest, Avg. Pace, Elev. Gain] for reference
    return leaderboard_elements

def add_runner(name_to_check, id_to_check):
    runner_id = database.insert_runner(name_to_check, id_to_check)
    return runner_id

def get_runners_list():
    return database.get_runners_list()

def get_individual_stats(Id):
    return scraper.get_stats(Id)