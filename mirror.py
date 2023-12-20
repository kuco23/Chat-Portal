from .entities import UserEntity, MessageEntity
from .database import Database
from .messaging import MessageService, Message

class Mirror:

    def __init__(self,
        social_platform: MessageService,
        database: Database
    ):
        self.social_platform = social_platform
        self.database = database

    def initNewUser(self, user_id: str) -> UserEntity:
        user = self.database.addUser(user_id)
        best_match = self._tryFindUserMatch(user, None)
        if best_match is not None: # match found
            self.database.matchUsers(user, best_match)
        return user

    def receiveMessage(self, from_user_id: str, message: Message):
        user = self.database.findUser(from_user_id)
        if user is None:
            user = self.initNewUser(from_user_id)
        if user.match is None:
            match = self._tryFindUserMatch(user, message.content)
            if match is not None:
                self.database.matchUsers(user, match)
            else: # no match possible => end here
                return
        self.social_platform.sendMessage(user.id, user.match.id, message.content)
        self.database.addMessage(user, user.match, message)

    ############################ INTERNAL METHODS ############################

    def _tryFindUserMatch(self, user: UserEntity, first_message: str | None) -> UserEntity | None:
        best_match = None
        best_score = -1
        for test_user in self.database.fetchMatchCandidates(user):
            score = self._scoreUserPair(user, test_user, first_message)
            if score > best_score:
                best_score = score
                best_match = test_user
        if self._scoreOkToMatch(best_score):
            return best_match

    def _scoreUserPair(self, user1: UserEntity, user2: UserEntity, user1_message: str | None) -> int:
        return 0

    # min score for two users to be considered a match
    @staticmethod
    def _scoreOkToMatch(score) -> bool:
        return score > 50