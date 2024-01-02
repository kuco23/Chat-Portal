from typing import List
from ..interface import ISocialPlatform
from .._entities import User
from .._models import MessageBatch
from .._entities import User, Message
from .. import Portal, Database


class MySocialPlatform(ISocialPlatform):
    sent: List[tuple]
    messages: List[MessageBatch]

    def __init__(self):
        self.messages = []
        self.sent = []

    def sendMessage(self, to_user: User, message: str):
        self.sent.append((to_user, message))
        return True

    def getNewMessages(self):
        return [self.messages.pop()]

    def getOldMessages(self):
        raise NotImplementedError()

    def getUser(self, user_id: str) -> User:
        return User(user_id, user_id)

platform = MySocialPlatform()
database = Database("sqlite+pysqlite:///:memory:")
portal = Portal(database, platform)

messageBatch = MessageBatch(User("1", "1"), [Message("1", "1", "Hi there", 0)])
platform.messages.append(messageBatch)
portal.runStep()

assert len(platform.messages) == 0
user1 = database.fetchUser("1")
assert user1 is not None
assert user1.id == "1"
assert user1.thread_id == "1"
assert user1.match_id is None
assert len(platform.sent) == 0

messageBatch = MessageBatch(User("2", "2"), [Message("2", "2", "Hi there too", 1)])
platform.messages.append(messageBatch)
portal.runStep()

user2 = database.fetchUser("2")
assert user2 is not None
assert user2.id == "2"
assert user2.thread_id == "2"
assert user2.match_id == "1"

assert len(platform.sent) == 2
to_user, msg = platform.sent[0]
assert msg == "Hi there"
assert to_user.id == "2"
to_user, msg = platform.sent[1]
assert msg == "Hi there too"
assert to_user.id == "1"

platform.sent.clear()
messageBatch = MessageBatch(User("1", "1"), [Message("3", "1", "Hi there again", 3)])
platform.messages.append(messageBatch)
portal.runStep()

assert len(platform.sent) == 1
to_user, msg = platform.sent[0]
assert msg == "Hi there again"
assert to_user.id == "2"
platform.sent.clear()

print("All tests for _portal.py passed")