import re

# Project imports
import scraper
import database
import bot

def get_ranking_name_and_distance(last_week=False):
    """ This will give ranking by distance for the desired week as a string"""
    leaderboard_elements = _parse_stats_from_table(last_week)


def _parse_stats_from_table(last_week=False):
    if last_week:
        table_rows = scraper.scrape_last_weekly_table()
    else:
        table_rows = scraper.scrape_weekly_table()
    
    leaderboard_elements=[]
    for row in table_rows:
        leaderboard_elements.append(re.split('(?<=\D)\s+(?=\d)|(?<=\d)\s+(?=\d)|\\n', row.text))
     # Remove header information of table, will also throw an error if no table exists
    leaderboard_elements.pop(0) 
    # [Rank, Athlete, Distance, Runs, Longest, Avg. Pace, Elev. Gain] for reference
    return leaderboard_elements

def get_week_stats(last_week=False):
    

def add_runner(name_to_check, id_to_check):
    runner_id = database.insert_runner(name_to_check, id_to_check)
    return runner_id