from typing import List
from ..interface import IPortal, ISocialPlatform, MessageBatch
from ._entities import User, ProcessedMessage
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
        self.database.addUsers(users)
        batches = self.social_platform.getNewMessages()
        for batch in batches:
            self._receiveMessageBatch(batch)

    def _receiveMessageBatch(self, messages: MessageBatch):
        if len(messages) == 0: return
        user = self.database.findUser(messages.from_user_id)
        # if user is not in the database, extract their info and add them
        # should not happen (messages should be received only from added users)
        if user is None:
            user = self.social_platform.getUser(messages.from_user_id)
            self.database.addUsers([user])
        # store messages to the database (they need to be available before match finding)
        for message in messages:
            self.database.addMessage(message, None)
        # try to match the user with another
        if user.match_id is None:
            match = self._tryFindUserMatch(user, messages)
            if match is not None:
                self.database.matchUsers(user.id, match.id)
                user.match_id = match.id
            else: # no match possible => end here
                return
        # if match is available, then process the message and send to the match
        self._processAndForwardMessages(user)

    def _processAndForwardMessages(self, user: User):
        assert user.match_id is not None, "user should have a match at message forward"
        unsent_messages = self.database.unsentMessagesFrom(user)
        processed_messages = self._processMessageBatch(MessageBatch(user.id, unsent_messages), user.match_id)
        assert len(processed_messages) == len(unsent_messages), "each message should be processed into exactly one other message"
        for original_message, processed_message in zip(unsent_messages, processed_messages):
            self.social_platform.sendMessage(user.match_id, processed_message.content)
            self.database.markMessageSent(original_message, user.match_id)
            self.database.addProcessedMessage(processed_message)

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
    def _processMessageBatch(self, messages: MessageBatch, to_user_id: str) -> List[ProcessedMessage]:
        return [ProcessedMessage(msg.id, msg.content) for msg in messages]

    def _scoreUserPair(self, user1: User, user2: User, user1_message_batch: str | MessageBatch) -> int:
        return 100

    # min score for two users to be considered a match
    @staticmethod
    def _scoreOkToMatch(score) -> bool:
        return score > 50