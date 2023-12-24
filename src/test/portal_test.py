from ..interface import ISocialPlatform, MessageBatch
from ..lib._entities import User, Message
from ..lib import Portal, Database


class MySocialPlatform(ISocialPlatform):
    cache = None
    def sendMessage(self, to_user_id: str, message: str):
        MySocialPlatform.cache = to_user_id, message
        return True

database = Database("sqlite+pysqlite:///:memory:")
platform = MySocialPlatform()
portal = Portal(database, platform)

user1 = User("user1")
portal.initNewUser(user1)
user = database.findUser("user1")
assert user is not None
assert user.match_id is None

user2 = User("user2")
portal.initNewUser(user2)
portal.receiveMessageBatch(MessageBatch("user1", [Message("1", "user1", "hello")]))
user = database.findUser(user1.id)
assert user is not None
assert user.match_id == "user2"
assert user.last_message_id == "1"
user = database.findUser(user2.id)
assert user is not None
assert user.match_id == "user1"
assert user.last_message_id is None

user3 = User("user3")
portal.initNewUser(user3)
user = database.findUser(user3.id)
assert user is not None
assert user.match_id is None

portal.receiveMessageBatch(MessageBatch("user1", [Message("2", "user1", "hello")]))
assert MySocialPlatform.cache == ("user2", "hello")

portal.receiveMessageBatch(MessageBatch("user2", [Message("3", "user2", "hi")]))
assert MySocialPlatform.cache == ("user1", "hi")
MySocialPlatform.cache = None

portal.receiveMessageBatch(MessageBatch("user3", [Message("4", "user3", "heya")]))
assert MySocialPlatform.cache is None

portal.receiveMessageBatch(MessageBatch("user1", [Message("5", "user1", "how are you?")]))
assert MySocialPlatform.cache == ("user2", "how are you?")

print("All tests for _portal.py passed")