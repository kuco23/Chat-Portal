from typing import List
from ..interface import ISocialPlatform
from .._entities import User, Thread, ReceivedMessage
from .._models import ReceivedMessageBatch
from .. import Database, GptPortal

sys_prompt = '''
Imagine you are a 60 year old woman named Sasha in the middle of an Instagram conversation. \
You've received a series of new messages, all from one person named "{from_name}". \
Modify these messages so that it appears as though they are being sent by you, Sasha, to another person named "{to_name}".

Key instructions:
1. Maintain the original meaning of each message.
2. Only alter parts of the messages that indicate the recipient is Sasha or the sender is "{from_name}". \
    Keep the rest of the message content unchanged. Avoid adding the recipient's name unnecessarily.
3. For unclear genders, avoid gender-specific language or assume both are male.
4. Use only English.
5. Respect the formatting: messages are separated by two blank lines. \
    Each original message corresponds to one modified message. \
    Messages before the "---" line are the context of the conversation, skip those in your output.\
'''

class MySocialPlatform(ISocialPlatform):
    messages: List[ReceivedMessageBatch]
    timestamp = 0

    def __init__(self):
        self.messages = []
        self.sent = []
        self.timestamp = 0

    def sendMessage(self, thread: Thread, message: str):
        print(thread.user_id + ":", message)

    def getNewMessages(self):
        return [self.messages.pop() for _ in range(len(self.messages))]

    def getOldMessages(self):
        raise NotImplementedError()

    def getUser(self, user_id: str) -> User:
        return User(user_id, full_name=user_id)

    def addMessage(self, thread: Thread, content: str):
        self.timestamp += 1
        message = ReceivedMessage(str(self.timestamp), thread.id, content, self.timestamp)
        self.messages.append(ReceivedMessageBatch([message], thread))

platform = MySocialPlatform()
database = Database("sqlite+pysqlite:///:memory:")
portal = GptPortal(database, platform, "gpt-4-0125-preview", sys_prompt)

thread1 = Thread("Nejc_thread", "Nejc")
thread2 = Thread("Hana_thread", "Hana")

thread = thread1
while True:
    x = input(thread.user_id + " > ")
    if x == "":
        portal.runStep()
        thread = thread2 if thread.id == thread1.id else thread1
        continue
    platform.addMessage(thread, x)
