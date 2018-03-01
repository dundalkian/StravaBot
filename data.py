from urllib import parse
import psycopg2
from configparser import ConfigParser
import os

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
    if os.environ['POST_USER']:
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

def insert_tables():
    commands = (
            """
            CREATE TABLE athletes (
                athlete_id SERIAL PRIMARY KEY,
                athlete_name VARCHAR(255) NOT NULL
            )
            """,
            """
            CREATE TABLE lift_types (
                lift_id SERIAL PRIMARY KEY,
                lift_name VARCHAR(255) NOT NULL
            )
            """,
            """
            CREATE TABLE lifts (
                lift_id SERIAL PRIMARY KEY,
                lift_name VARCHAR(255) NOT NULL,
                athlete_name VARCHAR(255) NOT NULL
                lift_weight INTEGER NOT NULL
            )
            """)

    try:
        # read the connection parameters
        params = config()
        # connect to the PostgreSQL server
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        # create table one by one
        for command in commands:
            cur.execute(command)
        # close communication with the PostgreSQL database server
        cur.close()
        # commit the changes
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()

def insert_athlete(athlete_name):
    sql = """INSERT INTO athletes(athlete_name) VALUES(%s) RETURNING athlete_id;"""
    conn = None
    athlete_id = None
    try:
        # read database configuration
        params = config()
        # connect to the PostgreSQL database
        conn = psycopg2.connect(**params)
        # create a new cursor
        cur = conn.cursor()
        # execute the INSERT statement
        cur.execute(sql, (athlete_name,))
        # get the generated id back
        athlete_id = cur.fetchone()[0]
        # commit the changes to the database
        conn.commit()
        # close communication with the database
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
 
    return athlete_id

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

def insert_lift_types(lift_name):
    sql = """INSERT INTO lift_types(lift_name) VALUES(%s) RETURNING lift_id;"""
    conn = None
    lift_type_id = None
    try:
        # read database configuration
        params = config()
        # connect to the PostgreSQL database
        conn = psycopg2.connect(**params)
        # create a new cursor
        cur = conn.cursor()
        # execute the INSERT statement
        cur.execute(sql, (lift_name,))
        # get the generated id back
        lift_type_id = cur.fetchone()[0]
        # commit the changes to the database
        conn.commit()
        # close communication with the database
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
 
    return lift_type_id

def insert_lift(athlete_name, lift_name, lift_weight):
    sql = """INSERT INTO lifts (athlete_name, lift_name, lift_weight) VALUES(%s, %s, %s) RETURNING lift_id;"""
    conn = None
    lift_id = None
    try:
        # read database configuration
        params = config()
        # connect to the PostgreSQL database
        conn = psycopg2.connect(**params)
        # create a new cursor
        cur = conn.cursor()
        # execute the INSERT statement
        cur.execute(sql, (athlete_name, lift_name, lift_weight))
        # get the generated id back
        lift_id = cur.fetchone()[0]
        # commit the changes to the database
        conn.commit()
        # close communication with the database
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
 
    return lift_id

def get_lift_pr(athlete_name, lift_name):
    """ query data from the vendors table """
    conn = None
    try:
        params = config()
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        cur.execute("SELECT lift_weight FROM lifts WHERE athlete_name=(%s) AND lift_name=(%s) ORDER BY lift_id;", (athlete_name, lift_name))
        print("The number of lifts: ", cur.rowcount)
        row = cur.fetchone()

        pr = 0
        while row is not None:
            if row[0] > pr:
                pr=row[0]
                print(pr)
            print(row)
            row = cur.fetchone()
 
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
    return pr

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

def get_lift_stats(athlete_name):
    major_lifts = ['squat', 'dl', 'row', 'bench', 'ohp']
    lift_prs = []
    for lift in major_lifts:
        lift_prs.append(get_lift_pr(athlete_name, lift))
    return lift_prs
