from ..lib._entities import User, Message
from ..lib import Database


database = Database("sqlite+pysqlite:///:memory:")

for user_id in ["user1", "user2", "user3"]:
    database.addUser(User(id=user_id))
    user = database.findUser(user_id)
    assert user is not None
    assert user.id == user_id
    assert user.match_id is None
    assert user.last_message_id is None

for i, user_id in enumerate(["user1", "user2", "user3"]):
    message = Message(id=str(i), from_user_id=user_id, content="hello")
    database.addMessage(user_id, message)
    user = database.findUser(user_id)
    assert user is not None
    assert user.id == user_id
    assert user.last_message_id == message.id

message = Message(id="4", from_user_id="user1", content="new message")
database.addMessage("user2", message)
user = database.findUser("user1")
assert user is not None
assert user.id == "user1"
assert user.last_message_id == message.id

database.matchUsers("user1", "user2")
for user_id in ["user1", "user2"]:
    user = database.findUser(user_id)
    assert user is not None
    assert user.id == user_id
    assert user.match_id == "user1" if user_id == "user2" else "user2"

user = database.findUser("user3")
assert user is not None
assert user.id == "user3"
assert user.match_id is None

print("All tests for _database.py passed")