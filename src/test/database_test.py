from ..lib import Database
from ..lib.interface import SocialMessage

SQLITE_INMEMORY_URL = "sqlite+pysqlite:///:memory:"

database = Database(SQLITE_INMEMORY_URL)

for user_id in ["user1", "user2", "user3"]:
    database.addUser(user_id)
    user = database.findUser(user_id)
    assert user is not None
    assert user.id == user_id
    assert user.match_id is None
    assert user.last_message is None

for i, user_id in enumerate(["user1", "user2", "user3"]):
    message = SocialMessage(str(i), user_id, "content")
    database.addMessage(user_id, message)
    user = database.findUser(user_id)
    assert user is not None
    assert user.id == user_id
    assert user.last_message is not None
    assert user.last_message.id == message.id

message = SocialMessage("4", "user1", "new message")
database.addMessage("user2", message)
user = database.findUser("user1")
assert user is not None
assert user.id == "user1"
assert user.last_message is not None
assert user.last_message.id == message.id

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
