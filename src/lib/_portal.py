from typing import List
from abc import ABC, abstractmethod
from src.lib._entities import User
from ..interface import IPortal, ISocialPlatform, IDatabase
from ._models import MessageBatch
from ._entities import User, ProcessedMessage
from ._logger import logger


class AbstractPortal(IPortal, ABC):
    database: IDatabase
    social_platform: ISocialPlatform

    def runStep(self):
        self._forwardUnsentMessages()
        batches = self.social_platform.getNewMessages()
        self._receiveMessageBatches(batches)

    def jumpstart(self):
        logger.info("Portal: jumpstarting")
        batches = self.social_platform.getOldMessages()
        self._receiveMessageBatches(batches)

    def _receiveMessageBatches(self, batches: List[MessageBatch]):
        for batch in batches:
            logger.info(f"Portal: handling {len(batch.messages)} length message batch from user {batch.from_user_id}")
            self._receiveMessageBatch(batch)
            logger.info(f"Portal: handled message batch from user {batch.from_user_id}")

    def _receiveMessageBatch(self, batch: MessageBatch):
        if len(batch.messages) == 0: return
        user = self.database.fetchUser(batch.from_user_id)
        # if user is not in the database, then add them
        if user is None:
            if type(batch.from_user) is str:
                # if only id is present, then fetch the user from the social platform
                user = self.social_platform.getUser(batch.from_user)
            elif type(batch.from_user) is User:
                # if all info is present, then add the user to the database
                user = batch.from_user
            else: return
            self.database.addUsers([user])
            logger.info(f"Portal: initialized new user {user.id} as a message batch sender")
        # store messages to the database (they need to be available before match finding)
        # note that messages sent before the latest message that is stored in the database
        # will not be stored (to not to process messages before database genesis)
        message_stack = sorted(batch.messages, key=lambda msg: -msg.timestamp)
        i = 0
        for message in message_stack:
            if self.database.fetchMessage(message.id) is not None: break
            i += 1
        self.database.addMessages(message_stack[:i])
        # try to match the user with another
        if user.match_id is None:
            match = self._bestMatchOf(user)
            if match is not None:
                self.database.matchUsers(user, match) # user entities are updated
                logger.info(f"Portal: assigned match {match.id} to user {user.id}")
                # if match's messages were processed before this user was available
                # (or matching criteria was not symmetric) then force-forward match's messages
                logger.info(f"Portal: forward messages from new match {match.id} to user {user.id}")
                self._forwardUserMessages(match)
            else: # no match possible => end here
                logger.info(f"Portal: could not assign a match to user {user.id}")
                return
        # if match is available, then process the message and send to the match
        logger.info(f"Portal: forward messages from user {user.id} to match {user.match_id}")
        self._forwardUserMessages(user)

    def _forwardUserMessages(self, user: User):
        if user.match_id is None: return
        unsent_messages = self.database.unsentMessagesFrom(user)
        if len(unsent_messages) == 0: return
        unsent_messages.sort(key=lambda msg: msg.timestamp)
        logger.info(f"Portal: processing {len(unsent_messages)} messages to be sent from user {user.id} to user {user.match_id}")
        processed_messages = self._processMessageBatch(MessageBatch(user.id, unsent_messages), user.match_id)
        # forward processed messages to the match
        last_unsent_index = 0
        for processed_message in processed_messages:
            self.social_platform.sendMessage(user.match_id, processed_message.content)
            # mark every message before processed_message.original_message_id as sent
            for i in range(last_unsent_index, len(unsent_messages)):
                original_message = unsent_messages[i]
                self.database.markMessageSent(original_message, user.match_id)
                last_unsent_index += 1
                if original_message.id == processed_message.original_message_id:
                    break
            # add processed message to the database
            self.database.addProcessedMessage(processed_message)
            logger.info(f"Portal: processed message {processed_message.id} sent to user {user.match_id}")
        # mark the rest of the messages as sent
        for i in range(last_unsent_index, len(unsent_messages)):
            self.database.markMessageSent(unsent_messages[i], user.match_id)

    def _forwardUnsentMessages(self):
        for user in self.database.fetchMatchedUsers():
            self._forwardUserMessages(user)

    ############################## Methods to override ##############################

    # tries to find a match for the given user
    # it should fetch the messages of user and each match candidate from the database
    # and find the most conversation-compatible ones using some algorithm (e.g. AI)
    @abstractmethod
    def _bestMatchOf(self, user: User) -> User | None:
        raise NotImplementedError()

    # processes the message sent to this.user before being forwarded to the sender's match
    # this is necessary, e.g. when this.user is a woman but sender and the match are men
    # e.g. the message is "how does a girl like you find herself on this app?"
    # the message forwarded to the match should be "how does a guy like you find himself on this app?"
    @abstractmethod
    def _processMessageBatch(self, batch: MessageBatch, to_user_id: str) -> List[ProcessedMessage]:
        raise NotImplementedError()


class Portal(AbstractPortal):

    def __init__(self,
        database: IDatabase,
        social_platform: ISocialPlatform
    ):
        self.database = database
        self.social_platform = social_platform

    def jumpstart(self):
        try:
            super().jumpstart()
        except Exception as e:
            logger.exception(f"Portal: exception occurred while jumpstarting: {e}")

    def runStep(self):
        try:
            super().runStep()
        except Exception as e:
            logger.exception(f"Portal: exception occurred while running step: {e}")

    def _receiveMessageBatches(self, batches: List[MessageBatch]):
        try:
            super()._receiveMessageBatches(batches)
        except Exception as e:
            logger.exception(f"ExceptionHandlerPortal: exception occurred while handling message batches: {e}")

    def _receiveMessageBatch(self, batch: MessageBatch):
        try:
            super()._receiveMessageBatch(batch)
        except Exception as e:
            logger.exception(f"ExceptionHandlerPortal: exception occurred while handling message batch: {e}")

    def _bestMatchOf(self, user: User) -> User | None:
        for test_user in self.database.fetchMatchCandidates(user.id):
            return test_user

    def _processMessageBatch(self, batch: MessageBatch, to_user_id: str) -> List[ProcessedMessage]:
        return [ProcessedMessage(message.id, message.content) for message in batch.messages]