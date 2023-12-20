from lib import Mirroring, SocialPlatform, Database, Message

database = Database()
social_platform = SocialPlatform()
mirroring = Mirroring(database, social_platform)

mirroring.initNewUser("user1")
mirroring.initNewUser("user2")
mirroring.initNewUser("user3")

mirroring.receiveMessage("user1", Message("1", "hello"))
mirroring.receiveMessage("user2", Message("2", "hi"))
