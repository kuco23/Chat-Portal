from .._entities import User, ReceivedMessage
from .. import Database

database = Database("sqlite+pysqlite:///:memory:")

for user_id in ["user1", "user2", "user3"]:
    database.addEntities([User(user_id, user_id)])
    user = database.fetchUser(user_id)
    assert user is not None
    assert user.id == user_id
    assert user.thread_id == user_id
    assert user.match_id is None

for i, user_id in enumerate(["user1", "user2", "user3"]):
    message = ReceivedMessage(str(i), user_id + "_thread", "hello", i)
    database.addEntities([message])
    message = database.fetchReceivedMessage(str(i))
    assert message is not None
    assert message.id == str(i)
    assert message.content == "hello"
    assert message.timestamp == i

assert (user1 := database.fetchUser("user1")) is not None
assert (user2 := database.fetchUser("user2")) is not None
database.matchUsers(user1, user2)
for user_id in ["user1", "user2"]:
    user = database.fetchUser(user_id)
    assert user is not None
    assert user.id == user_id
    assert user.match_id == "user1" if user_id == "user2" else "user2"

user = database.fetchUser("user3")
assert user is not None
assert user.id == "user3"
assert user.match_id is None

print("All tests for _database_basic_test.py passed")