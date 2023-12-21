from ..lib import Mirroring, Database
from ..lib.interface import ISocialPlatform, SocialMessage

SQLITE_INMEMORY_URL = "sqlite+pysqlite:///:memory:"

class MySocialPlatform(ISocialPlatform):
    cache = None
    def sendMessage(self, to_user_id: str, message: str):
        MySocialPlatform.cache = to_user_id, message

database = Database(SQLITE_INMEMORY_URL)
platform = MySocialPlatform()
mirroring = Mirroring(database, platform)

mirroring.initNewUser("user1")
user = database.findUser("user1")
assert user is not None
assert user.match_id is None

mirroring.initNewUser("user2")
user1 = database.findUser("user1")
user2 = database.findUser("user2")
assert user1 is not None
assert user1.match_id == "user2"
assert user2 is not None
assert user2.match_id == "user1"

mirroring.initNewUser("user3")
user = database.findUser("user3")
assert user is not None
assert user.match_id is None

mirroring.receiveMessage(SocialMessage("1", "user1", "hello"))
assert MySocialPlatform.cache == ("user2", "hello")

mirroring.receiveMessage(SocialMessage("2", "user2", "hi"))
assert MySocialPlatform.cache == ("user1", "hi")
MySocialPlatform.cache = None

mirroring.receiveMessage(SocialMessage("3", "user3", "heya"))
assert MySocialPlatform.cache is None

mirroring.receiveMessage(SocialMessage("4", "user1", "how are you?"))
assert MySocialPlatform.cache == ("user2", "how are you?")