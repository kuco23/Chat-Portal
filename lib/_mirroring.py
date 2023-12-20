from ._objects import Message, User
from ._entities import UserEntity
from ._database import Database
from ._messaging import SocialPlatform

class Mirroring:

    def __init__(self,
        database: Database,
        social_platform: SocialPlatform
    ):
        self.database = database
        self.social_platform = social_platform

    def initNewUser(self, user_id: str) -> User:
        user = self.database.addUser(user_id)
        best_match = self._tryFindUserMatch(user, None)
        if best_match is not None: # match found
            self.database.matchUsers(user.id, best_match.id)
        return user

    def receiveMessage(self, from_user_id: str, message: Message):
        user = self.database.findUser(from_user_id)
        if user is None:
            user = self.initNewUser(from_user_id)
        if user.match_id is None:
            match = self._tryFindUserMatch(user, message.content)
            if match is not None:
                self.database.matchUsers(user.id, match.id)
                user.match_id = match.id
            else: # no match possible => end here
                return
        self.social_platform.sendMessage(user.id, user.match_id, message.content)
        self.database.addMessage(user.id, message)

    ############################ INTERNAL METHODS ############################

    def _tryFindUserMatch(self, user: User, first_message: str | None) -> User | None:
        best_match = None
        best_score = -1
        for test_user in self.database.fetchMatchCandidates(user.id):
            score = self._scoreUserPair(user, test_user, first_message)
            if score > best_score:
                best_score = score
                best_match = test_user
        if self._scoreOkToMatch(best_score):
            return best_match

    def _scoreUserPair(self, user1: User, user2: User, user1_message: str | None) -> int:
        return 100

    # min score for two users to be considered a match
    @staticmethod
    def _scoreOkToMatch(score) -> bool:
        return score > 50