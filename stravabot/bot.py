import json
import os
import time
import datetime
import threading
import re
from configparser import ConfigParser

from fbchat import Client
from fbchat.models import Message, ThreadType

# project imports
import data_handler


class StravaBot(Client):
    all_runners = {}
    current_running_chad = ''

    def pmMe(self, txt):
        self.send(Message(text=txt), thread_id=client.uid,
                  thread_type=ThreadType.USER)

    def onMessage(self, author_id, message_object, thread_id, thread_type, **kwargs):
        if message_object.text is not None:
            messageText = message_object.text.lower()
            if re.match("(?i)ghoul", messageText):
                print(messageText)
                response = data_handler.process_message(self, author_id, messageText, thread_id, thread_type)
                self.send(Message(text=response), thread_id, thread_type)
            else:
                # Sends the data to the inherited onMessage, so that we can still see when a message is recieved
                super(StravaBot, self).onMessage(author_id=author_id, message_object=message_object,
                                                 thread_id=thread_id, thread_type=thread_type, **kwargs)


def config(filename='config.ini', section='facebookcredentials'):
    # create a parser
    parser = ConfigParser()
    # read config file
    parser.read(filename)

    # get section
    creds = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            creds[param[0]] = param[1]
    elif os.environ['EMAIL']:
        creds['email'] = os.environ['EMAIL']
        creds['password'] = os.environ['PASSWORD']
    else:
        raise Exception(
            'Section {0} not found in the {1} file'.format(section, filename))
    return creds


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


next_call = time.time()


def update_loop():
    global next_call
    print("Starting timer to next loop: {}".format(datetime.datetime.now()))
    while True:
        try:
            data_handler.update_tables()
        except Exception as e:
            print("Selenium failed, retrying, hopefully it works soon :/")
            print(e)
            continue
        print("Selenium succeeded (maybe)")
        break
    next_call = next_call + 300
    threading.Timer(next_call-time.time(), update_loop).start()


creds = config()
client = startupClient(creds['email'], creds['password'])
StravaBot.all_runners = data_handler.get_runners_list()
print(StravaBot.all_runners)
data_handler.findChad(client)
#update_loop()
client.listen()
