from urllib import parse
import psycopg2
from configparser import ConfigParser
import os
import StravaData

def config(filename='database.ini', section='postgresql'):
    # create a parser
    parser = ConfigParser()
    # read config file
    parser.read(filename)
 
    # get section, default to postgresql
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    elif os.environ['POST_USER']:
        db['host'] = os.environ['POST_HOST']
        db['database'] = os.environ['POST_DATABASE']
        db['user'] = os.environ['POST_USER']
        db['password'] = os.environ['POST_PASSWORD']
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))
    return db

def connect():
    """ Connect to the PostgreSQL database server """
    conn = None
    try:
        # read connection parameters
        params = config()
 
        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(**params)
 
        # create a cursor
        cur = conn.cursor()
        
 # execute a statement
        print('PostgreSQL database version:')
        cur.execute('SELECT version()')
 
        # display the PostgreSQL database server version
        db_version = cur.fetchone()
        print(db_version)
       
     # close the communication with the PostgreSQL
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            print('Database connection closed.')

# (For reference and if I blow up prod db :yikes:)
def insert_tables():
    command = """
            CREATE TABLE weekly_stats (
                rank SERIAL PRIMARY KEY,
                athlete VARCHAR(255) NOT NULL,
                distance VARCHAR(255) NOT NULL,
                num_runs VARCHAR NOT NULL,
                longest_run VARCHAR(255) NOT NULL,
                avg_pace VARCHAR(255) NOT NULL,
                elev_gain VARCHAR(255) NOT NULL
            )"""
    conn = None
    try:
        # read the connection parameters
        params = config()
        # connect to the PostgreSQL server
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        # create table one by one
        cur.execute(command)
        # commit the changes
        conn.commit()
        # close communication with the PostgreSQL database server
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()

def update_weekly_table():
    remove_stats_sql = """DELETE FROM weekly_stats;"""
    new_stats_sql = """INSERT INTO weekly_stats (rank, athlete, distance, num_runs, longest_run, avg_pace, elev_gain) VALUES(%s, %s, %s, %s, %s, %s, %s);"""
    conn = None
    weekly_stats = StravaData.get_weekly_stats()
    try:
        # read database configuration
        params = config()
        # connect to the PostgreSQL database
        conn = psycopg2.connect(**params)
        # create a new cursor
        cur = conn.cursor()
        # delete old records
        cur.execute(remove_stats_sql)
        # execute the INSERT statement
        for runner_stats in weekly_stats:
            cur.execute(new_stats_sql, runner_stats)
        # commit the changes to the database
        conn.commit()
        # close communication with the database
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
 
    return True

def get_weekly_table():
    conn = None
    try:
        params = config()
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        cur.execute("SELECT rank, athlete, distance, num_runs, longest_run, avg_pace, elev_gain FROM weekly_stats;")
        weekly_table = cur.fetchall()

        print(weekly_table)
 
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()

    return(weekly_table)

def insert_runner(runner_name, runner_strava_id):
    sql = """INSERT INTO runners (runner_name, runner_strava_id) VALUES(%s, %s) RETURNING runner_id;"""
    conn = None
    runner_id = None
    try:
        # read database configuration
        params = config()
        # connect to the PostgreSQL database
        conn = psycopg2.connect(**params)
        # create a new cursor
        cur = conn.cursor()
        # execute the INSERT statement
        cur.execute(sql, (runner_name, runner_strava_id))
        # get the generated id back
        runner_id = cur.fetchone()[0]
        # commit the changes to the database
        conn.commit()
        # close communication with the database
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
 
    return runner_id

def get_runners_list():
    """Get list of ALL runners and Strava Id's"""
    conn = None
    try:
        params = config()
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        cur.execute("SELECT runner_name, runner_strava_id FROM runners;")
        print("The number of runners: ", cur.rowcount)
        all_runners = cur.fetchall()

        print(all_runners)
 
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()

    return(all_runners)

