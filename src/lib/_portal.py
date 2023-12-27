from typing import List
from time import sleep
from ..interface import IPortal, ISocialPlatform, IDatabase
from ._models import MessageBatch
from ._entities import User, ProcessedMessage
from ._logger import logger


class Portal(IPortal):
    database: IDatabase
    social_platform: ISocialPlatform

    def __init__(self,
        database: IDatabase,
        social_platform: ISocialPlatform
    ):
        self.database = database
        self.social_platform = social_platform

    def runStep(self):
        self._processUnsentMessages()
        self._handleMessageBatches(False)

    def jumpstart(self):
        self._handleMessageBatches(True)

    def _handleMessageBatches(self, old: bool):
        batches = self.social_platform.getOldMessages() if old \
            else self.social_platform.getNewMessages()
        logger.info(f"Portal: received {len(batches)} {'old' if old else 'new'} message batches")
        for batch in batches:
            logger.info(f"Portal: processing message batch from user {batch.from_user_id}")
            self._receiveMessageBatch(batch)
            logger.info(f"Portal: processed message batch from user {batch.from_user_id}")

    def _receiveMessageBatch(self, messages: MessageBatch) -> User | None:
        if len(messages) == 0: return
        user = self.database.findUser(messages.from_user_id)
        # if user is not in the database, then add it
        if user is None:
            if type(messages.from_user) is str:
                # if only id is present, then fetch the user from the social platform
                user = self.social_platform.getUser(messages.from_user)
            elif type(messages.from_user) is User:
                # if all info is present, then add the user to the database
                user = messages.from_user
            else: return
            self.database.addUsers([user])
            logger.info(f"Portal: initialized new user {user.id} as a message batch sender")
        # store messages to the database (they need to be available before match finding)
        # note that the message should not be stored if it is already in the database
        for message in messages:
            self.database.addMessageIfNotExists(message, None)
        # try to match the user with another
        if user.match_id is None:
            match = self._tryFindUserMatch(user, messages)
            if match is not None:
                self.database.matchUsers(user.id, match.id)
                user.match_id = match.id
                match.match_id = user.id
                logger.info(f"Portal: assigned match {match.id} to user {user.id}")
                # if match's messages were processed before this user was available
                # (or matching was not symmetric) then force-forward match's messages
                # note that messages will not be double-sent because sending them
                # is logged in the database
                logger.info(f"Portal: forward messages from match {match.id} to user {match.id}")
                self._processAndForwardMessagesFrom(match)
            else: # no match possible => end here
                logger.info(f"Portal: could not assign a match to user {user.id}")
                return
        # if match is available, then process the message and send to the match
        logger.info(f"Portal: forward messages from user {user.id} to match {user.match_id}")
        self._processAndForwardMessagesFrom(user)

    def _processUnsentMessages(self):
        for user in self.database.fetchMatchedUsers():
            self._processAndForwardMessagesFrom(user)

    def _processAndForwardMessagesFrom(self, user: User):
        if user.match_id is None: return
        unsent_messages = self.database.unsentMessagesFrom(user)
        if len(unsent_messages) == 0: return
        logger.info(f"Portal: processing messages to be sent from user {user.id} to user {user.match_id}")
        processed_messages = self._processMessageBatch(MessageBatch(user.id, unsent_messages), user.match_id)
        if len(processed_messages) != len(unsent_messages):
            return logger.error(f"Portal: processed messages length does not match the unprocessed ones")
        for original_message, processed_message in zip(unsent_messages, processed_messages):
            sleep(self._waitToType(processed_message.content))
            self.social_platform.sendMessage(user.match_id, processed_message.content)
            self.database.markMessageSent(original_message, user.match_id)
            self.database.addProcessedMessage(processed_message)
            logger.info(f"Portal: processed message {processed_message.id} sent to user {user.match_id}")

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

    @staticmethod
    def _waitToType(word: str) -> int:
        return len(word) // 3