from typing import List
from ..interface import IPortal, ISocialPlatform, MessageBatch
from ._entities import User
from ._database import Database


class Portal(IPortal):

    def __init__(self,
        database: Database,
        social_platform: ISocialPlatform
    ):
        self.database = database
        self.social_platform = social_platform

    def runStep(self):
        users = self.social_platform.getNewUsers()
        for user in users:
            self.initNewUser(user)
        messages = self.social_platform.getNewMessages()
        for message in messages:
            self.receiveMessageBatch(message)

    def initNewUser(self, user: User):
        self.database.addUser(user)

    def receiveMessageBatch(self, messages: MessageBatch):
        if len(messages) == 0: return
        user = self.database.findUser(messages.from_user_id)
        if user is None:
            # should not happen (messages should be received only from added users)
            user = self.social_platform.getUser(messages.from_user_id)
            self.initNewUser(user)
        if user.match_id is None:
            match = self._tryFindUserMatch(user, messages)
            if match is not None:
                self.database.matchUsers(user.id, match.id)
                user.match_id = match.id
            else: # no match possible => end here
                return
        processed_messages = self._processMessageBatch(messages, user.match_id)
        for processed_message in processed_messages:
            self.social_platform.sendMessage(user.match_id, processed_message)
        self.database.addMessage(user.match_id, messages.socialMessages[-1])

    def _tryFindUserMatch(self, user: User, initial_message_batch: MessageBatch) -> User | None:
        best_match = None
        best_score = -1
        for test_user in self.database.fetchMatchCandidates(user.id):
            score = self._scoreUserPair(user, test_user, initial_message_batch)
            if score > best_score:
                best_score = score
                best_match = test_user
        if self._scoreOkToMatch(best_score):
            return best_match

    # processes the message sent to this.user before being forwarded to the sender's match
    # this is necessary, e.g. when this.user is a woman but sender and the match are men
    # e.g. the message is "how does a girl like you find herself on this app?"
    # the message forwarded to the match should be "how does a guy like you find himself on this app?"
    def _processMessageBatch(self, messages: MessageBatch, to_user_id: str) -> List[str]:
        return [msg.content for msg in messages]

    def _scoreUserPair(self, user1: User, user2: User, user1_message_batch: str | MessageBatch) -> int:
        return 100

    # min score for two users to be considered a match
    @staticmethod
    def _scoreOkToMatch(score) -> bool:
        return score > 50