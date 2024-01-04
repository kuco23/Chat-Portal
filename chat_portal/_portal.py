from typing import Optional, List
from .interface import IPortal, ISocialPlatform, IDatabase
from ._models import MessageBatch
from ._entities import User, ProcessedMessage
from ._logger import logger


class AbstractPortal(IPortal):
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
            logger.info(f"Portal: handling {len(batch.messages)} length message batch from user {batch.from_user.id}")
            self._receiveMessageBatch(batch)
            logger.info(f"Portal: handled message batch from user {batch.from_user.id}")

    # think before changing the order of the included methods
    def _receiveMessageBatch(self, batch: MessageBatch):
        if len(batch.messages) == 0: return
        user = self._fetchOrCreateUser(batch.from_user) # redefine user with the actual db entity!
        self._storeNewMessages(batch) # store new messages, so they are available in the next steps
        if self._matchAvailable(user): # check if user can be (or already is) matched
            self._forwardUserMessages(user) # forward unsent messages to user's match

    def _forwardUnsentMessages(self):
        for user in self.database.fetchMatchedUsers():
            self._forwardUserMessages(user)

    def _forwardUserMessages(self, user: User):
        assert user.match_id is not None
        assert (match := self.database.fetchUser(user.match_id)) is not None
        unsent_messages = self.database.unsentMessagesFrom(user)
        if len(unsent_messages) == 0: return
        unsent_messages.sort(key=lambda msg: msg.timestamp)
        logger.info(f"Portal: processing {len(unsent_messages)} messages to be sent from user {user.id} to user {match.id}")
        processed_messages = self._processMessageBatch(MessageBatch(user, unsent_messages), match)
        logger.info(f"Portal: sending {len(processed_messages)} processed messages from user {user.id} to user {match.id}")
        # forward processed messages to the match
        last_unsent_index = 0
        for processed_message in processed_messages:
            self.social_platform.sendMessage(match, processed_message.content)
            # mark every message before processed_message.original_message_id as sent
            for i in range(last_unsent_index, len(unsent_messages)):
                original_message = unsent_messages[i]
                self.database.markMessageSent(original_message, match)
                last_unsent_index += 1
                if original_message.id == processed_message.original_message_id:
                    break
            # add processed message to the database
            self.database.addProcessedMessage(processed_message)
            logger.info(f"Portal: processed message {processed_message.id} sent to user {match.id}")
        # mark the rest of the messages as sent
        for i in range(last_unsent_index, len(unsent_messages)):
            self.database.markMessageSent(unsent_messages[i], match)

    def _fetchOrCreateUser(self, _user: User) -> User:
        user = self.database.fetchUser(_user.id)
        if user is None:
            self.database.addUsers([_user])
            assert (user := self.database.fetchUser(_user.id)) is not None
            logger.info(f"Portal: initialized new user {user.id}")
        return user

    def _storeNewMessages(self, batch: MessageBatch):
        # messages sent before the latest message that is stored in the database
        # will not be stored (to not to process messages before database genesis)
        message_stack = sorted(batch.messages, key=lambda msg: -msg.timestamp)
        i = 0
        for message in message_stack:
            if self.database.fetchMessage(message.id) is not None: break
            i += 1
        self.database.addMessages(message_stack[:i])

    def _matchAvailable(self, user: User) -> bool:
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
                return False
        return True


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

    def _bestMatchOf(self, user: User) -> Optional[User]:
        for test_user in self.database.fetchMatchCandidates(user.id):
            return test_user

    def _processMessageBatch(self, batch: MessageBatch, to_user: User) -> List[ProcessedMessage]:
        return [ProcessedMessage(message.id, message.content) for message in batch.messages]