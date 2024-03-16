from .._entities import User, ReceivedMessage, ModifiedMessage
from .. import Database

database = Database("sqlite+pysqlite:///:memory:")

database.addEntities([User("0", "user0_thread"), User("1", "user1_thread")])
user0 = database.fetchUser("0")
user1 = database.fetchUser("1")
assert user0 is not None
assert user1 is not None
database.matchUsers(user0, user1)

database.addEntities([
    ReceivedMessage("0", "user0_thread", "(user0) hi", 1),
    ReceivedMessage("1", "user0_thread", "(user0) how u doin?", 3),
    ReceivedMessage("2", "user0_thread", "(user0) I'm well, how are you", 6)
])
database.addEntities([
    ModifiedMessage("0", "user1_thread", "(modified) (user0) hi", 4),
    ModifiedMessage("1", "user1_thread", "(modified) (user0) how u doin?", 5)
])
database.addEntities([
    ReceivedMessage("3", "user1_thread", "(user1) hi", 10),
    ReceivedMessage("4", "user1_thread", "(user1) I'm well, how are you", 12),
    ReceivedMessage("5", "user1_thread", "(user1) Yeaaaaah", 13)
])
database.addEntities([
    ModifiedMessage("2", "user0_thread", "(modified) (user1) hi", 2),
    ModifiedMessage("3", "user0_thread", "(modified) (user1) I'm well, how are you", 14),
    ModifiedMessage("4", "user0_thread", "(modified) (user1) Yeaaaaah", 16)
])

user0_conversation = database.conversationHistory("user0_thread", 14, 3)
assert len(user0_conversation) == 5
assert user0_conversation[0].timestamp == 2
assert user0_conversation[1].timestamp == 3
assert user0_conversation[2].timestamp == 6
assert user0_conversation[3].timestamp == 14
assert user0_conversation[4].timestamp == 16

user1_conversation = database.conversationHistory("user1_thread", 10, 1)
assert len(user1_conversation) == 4
assert user1_conversation[0].timestamp == 5
assert user1_conversation[1].timestamp == 10
assert user1_conversation[2].timestamp == 12
assert user1_conversation[3].timestamp == 13

print("All tests for _database_conversation_test.py passed")