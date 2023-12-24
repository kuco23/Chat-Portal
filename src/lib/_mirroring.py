from time import sleep
from .interface import IMirroring, ISocialPlatform, SocialMessage, SocialUser
from ._database import Database


class Mirroring(IMirroring):

    def __init__(self,
        database: Database,
        social_platform: ISocialPlatform
    ):
        self.database = database
        self.social_platform = social_platform

    def runStep(self):
        """
        Main loop - listens for the messages
        """
        users = self.social_platform.getNewUsers()
        for user in users:
            self.initNewUser(user)
        messages = self.social_platform.getNewMessages()
        for message in messages:
            self.receiveMessage(message)

    def initNewUser(self, user: SocialUser):
        self.database.addUser(user)

    def receiveMessage(self, message: SocialMessage):
        user = self.database.findUser(message.from_user_id)
        if user is None:
            # this case should not really happen, because
            # before message received, user should be added
            user = self.social_platform.getUser(message.from_user_id)
            self.initNewUser(user)
        if user.match_id is None:
            match = self._tryFindUserMatch(user, message.content)
            if match is not None:
                self.database.matchUsers(user.id, match.id)
                user.match_id = match.id
            else: # no match possible => end here
                return
        processed_message = self._processMessage(message, user.match_id)
        if self.social_platform.sendMessage(user.match_id, processed_message):
            self.database.addMessage(user.match_id, message)

    def _tryFindUserMatch(self, user: SocialUser, first_message: str) -> SocialUser | None:
        best_match = None
        best_score = -1
        for test_user in self.database.fetchMatchCandidates(user.id):
            score = self._scoreUserPair(user, test_user, first_message)
            if score > best_score:
                best_score = score
                best_match = test_user
        if self._scoreOkToMatch(best_score):
            return best_match

    # processes the message sent to this.user before being forwarded to the sender's match
    # this is necessary, e.g. when this.user is a woman but sender and the match are men
    # e.g. the message is "how does a girl like you find herself on this app?"
    # the message forwarded to the match should be "how does a guy like you find himself on this app?"
    def _processMessage(self, message: SocialMessage, to_user_id: str) -> str:
        return message.content

    def _scoreUserPair(self, user1: SocialUser, user2: SocialUser, user1_message: str | None) -> int:
        return 100

    # min score for two users to be considered a match
    @staticmethod
    def _scoreOkToMatch(score) -> bool:
        return score > 50