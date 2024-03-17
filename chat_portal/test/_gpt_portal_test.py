from typing import List
from ..interface import ISocialPlatform
from .._entities import User, ReceivedMessage
from .._models import ReceivedMessageBatch
from .. import Database, GptPortal

class MySocialPlatform(ISocialPlatform):
    messages: List[ReceivedMessageBatch]
    timestamp = 0

    def __init__(self):
        self.messages = []
        self.sent = []
        self.timestamp = 0

    def sendMessage(self, to_user: User, message: str):
        print(to_user.full_name + ":", message)

    def getNewMessages(self):
        return [self.messages.pop() for _ in range(len(self.messages))]

    def getOldMessages(self):
        raise NotImplementedError()

    def getUser(self, user_id: str) -> User:
        return User(user_id, user_id)

    def addMessage(self, user: User, content: str):
        self.timestamp += 1
        message = ReceivedMessage(str(self.timestamp), user.thread_id, content, self.timestamp)
        self.messages.append(ReceivedMessageBatch(user, [message]))


platform = MySocialPlatform()
database = Database("sqlite+pysqlite:///:memory:")
portal = GptPortal(database, platform, "gpt-4-0125-preview")

user1 = User("1", "1", full_name="Nejc")
user2 = User("2", "2", full_name="Hana")

user = user1
while True:
    x = input(user.full_name + " > ")
    if x == "":
        portal.runStep()
        user = user2 if user.id == user1.id else user1
        continue
    platform.addMessage(user, x)
