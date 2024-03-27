from typing import List
from ..interface import ISocialPlatform
from .._entities import User, Thread, ReceivedMessage
from .._models import ReceivedMessageBatch
from .. import Portal, Database


class MySocialPlatform(ISocialPlatform):
    sent: List[tuple]
    received: List[ReceivedMessageBatch]

    def __init__(self):
        self.received = []
        self.sent = []

    def sendMessage(self, thread: Thread, message: str):
        self.sent.append((thread, message))
        return True

    def getNewMessages(self):
        return [self.received.pop()]

    def getOldMessages(self):
        raise NotImplementedError()

    def getUser(self, user_id: str) -> User:
        return User(user_id)

platform = MySocialPlatform()
database = Database("sqlite+pysqlite:///:memory:")
portal = Portal(database, platform)

messageBatch = ReceivedMessageBatch([
    ReceivedMessage("1", "user1_thread", "Hi there", 0)
], Thread("user1_thread", "user1"), User("user1"))
platform.received.append(messageBatch)
portal.runStep()

assert len(platform.received) == 0
thread1 = database.fetchThread("user1_thread")
assert thread1 is not None
assert thread1.user_id == "user1"
assert thread1.pair_id is None
assert len(platform.sent) == 0

messageBatch = ReceivedMessageBatch([
    ReceivedMessage("2", "user2_thread", "Hi there too", 1)
], Thread("user2_thread", "user2"), User("user2"))
platform.received.append(messageBatch)
portal.runStep()

thread2 = database.fetchThread("user2_thread")
assert thread2 is not None
assert thread2.user_id == "user2"
assert thread2.pair_id == "user1_thread"

assert len(platform.sent) == 2
platform.sent.sort(key = lambda x: x[0].id)
to_thread, msg = platform.sent[0]
assert msg == "Hi there too"
assert to_thread.id == "user1_thread"
to_thread, msg = platform.sent[1]
assert msg == "Hi there"
assert to_thread.id == "user2_thread"

platform.sent.clear()
messageBatch = ReceivedMessageBatch([
    ReceivedMessage("3", "user1_thread", "Hi there again", 3)
], Thread("user1_thread", "user1"))
platform.received.append(messageBatch)
portal.runStep()

assert len(platform.sent) == 1
to_thread, msg = platform.sent[0]
assert msg == "Hi there again"
assert to_thread.id == "user2_thread"
platform.sent.clear()

print("All tests for _portal.py passed")