import json
import os
import time
import datetime
import threading
import re

from fbchat import Client
from fbchat.models import Message, ThreadType

# project imports
import data_handler

email = os.environ['EMAIL']
password = os.environ['PASSWORD']


class StravaBot(Client):
    all_runners = {}
    current_running_chad = ''

    def pmMe(self, txt):
        self.send(Message(text=txt), thread_id=client.uid,
                  thread_type=ThreadType.USER)

    def onMessage(self, author_id, message_object, thread_id, thread_type, **kwargs):
        if message_object.text is not None:
            messageText = message_object.text
            if re.match("(?i)ghoul", messageText):
                response = data_handler.process_message(
                    self, author_id, messageText, thread_id, thread_type)
                self.send(Message(text=response), thread_id, thread_type)
            else:
                # Sends the data to the inherited onMessage, so that we can still see when a message is recieved
                super(StravaBot, self).onMessage(author_id=author_id, message_object=message_object,
                                                 thread_id=thread_id, thread_type=thread_type, **kwargs)


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


# Reving up the engines #


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


client = startupClient(email, password)
data_handler.get_runners_list()
data_handler.findChad(client)
update_loop()
client.listen()
