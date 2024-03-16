from typing import Optional, List, Dict, Tuple
from .interface import IPortal, ISocialPlatform, IDatabase
from ._models import ReceivedMessageBatch
from ._entities import User, ReceivedMessage, ModifiedMessage
from ._logger import logger


# assumes all messages fetched from database are ordered by timestamp

class AbstractPortal(IPortal):
    database: IDatabase
    social_platform: ISocialPlatform

    def runStep(self):
        self._forceForwardMessages()
        batches = self.social_platform.getNewMessages()
        self._receiveMessageBatches(batches)

    def jumpstart(self):
        logger.info("Portal: jumpstarting")
        batches = self.social_platform.getOldMessages()
        self._receiveMessageBatches(batches)

    def _receiveMessageBatches(self, batches: List[ReceivedMessageBatch]):
        for batch in batches:
            logger.info(f"Portal: handling {len(batch.messages)} length message batch from user {batch.from_user.id}")
            self._receiveMessageBatch(batch)
            logger.info(f"Portal: handled message batch from user {batch.from_user.id}")

    # think before changing the order of the method's function calls
    def _receiveMessageBatch(self, batch: ReceivedMessageBatch):
        if len(batch.messages) == 0: return
        # redefine user with the actual db entity!
        user = self._fetchOrCreateUser(batch.from_user)
        # store new messages, so they are available in the next steps
        self._storeReceivedMessages(batch.messages)
        match, exists = self._getMatchIfNewWithExistenceStatus(user)
        # if user cannot be matched, end here
        if not exists: return
        self._pushForwardMessages(user)
        # if match's messages were processed before this user was available
        # (or matching criteria was not symmetric) then force-forward match's messages
        if match is not None:
            logger.info(f"Portal: forward messages from new match {match.id} to user {user.id}")
            self._pushForwardMessages(match)

    def _forceForwardMessages(self):
        for user in self.database.matchedUsers():
            self._pushForwardMessages(user)

    def _pushForwardMessages(self, user: User):
        assert user.match_id is not None
        assert (match := self.database.fetchUser(user.match_id)) is not None
        self._processReceivedMessages(user, match)
        self._forwardModifiedMessages(match)

    def _processReceivedMessages(self, user: User, match: User):
        unprocessed_messages = self.database.unprocessedMessagesFrom(user)
        unprocessed_messages.sort(key=lambda msg: msg.timestamp)
        if len(unprocessed_messages) == 0: return
        if not self._messagesReadyToBeProcessed(unprocessed_messages, user, match): return
        logger.info(f"Portal: modifying {len(unprocessed_messages)} messages from user {user.id}")
        modified_messages = self._modifyUnsentMessages(unprocessed_messages, user, match)
        logger.info(f"Portal: modified {len(modified_messages)} messages from user {user.id}")
        # store modified messages in database and mark unprocessed messages as processed
        logger.info(f"Portal: updating the database after processing received messages from user {user.id}")
        for unprocessed_message in unprocessed_messages:
            self.database.markMessageProcessed(unprocessed_message)
        self.database.addEntities(modified_messages)

    def _forwardModifiedMessages(self, match: User):
        modified_messages = self.database.unsentMessagesTo(match)
        for message in modified_messages:
            self.social_platform.sendMessage(match, message.content)
            logger.info(f"Portal: forwarded message {message.id} to user {match.id}")
            self.database.markMessageSent(message)

    def _fetchOrCreateUser(self, _user: User) -> User:
        user = self.database.fetchUser(_user.id)
        if user is None:
            self.database.addEntities([_user])
            assert (user := self.database.fetchUser(_user.id)) is not None
            logger.info(f"Portal: initialized new user {user.id}")
        return user

    def _storeReceivedMessages(self, messages: List[ReceivedMessage]):
        # messages sent before the latest message that is stored in the database
        # will not be stored (to not to process messages before database genesis)
        message_stack = sorted(messages, key=lambda msg: -msg.timestamp)
        i = 0
        for message in message_stack:
            if self.database.fetchReceivedMessage(message.id) is not None: break
            i += 1
        self.database.addEntities(message_stack[:i])

    # tries to fetch the match or create it and returns it if it's newly created,
    # along with a flag telling if the match exists
    def _getMatchIfNewWithExistenceStatus(self, user: User) -> Tuple[Optional[User], bool]:
        if user.match_id is None:
            match = self._bestMatchOf(user)
            if match is not None:
                self.database.matchUsers(user, match) # user entities are updated
                logger.info(f"Portal: assigned match {match.id} to user {user.id}")
                return match, True
            else: # no match possible => end here
                logger.info(f"Portal: could not assign a match to user {user.id}")
                return None, False
        return None, True

def exceptWrapper(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(f"Portal: exception occurred while calling {func.__name__}: {e}")
    return wrapper

class Portal(AbstractPortal):
    _delay_messages_from: Dict[str, int] # time to delay forwarding of messages from user to match

    def __init__(self,
        database: IDatabase,
        social_platform: ISocialPlatform
    ):
        self.database = database
        self.social_platform = social_platform
        self._delay_messages_from = dict()

    @exceptWrapper
    def jumpstart(self):
        super().jumpstart()

    @exceptWrapper
    def runStep(self):
        super().runStep()

    @exceptWrapper
    def _receiveMessageBatches(self, batches: List[ReceivedMessageBatch]):
        super()._receiveMessageBatches(batches)

    @exceptWrapper
    def _receiveMessageBatch(self, batch: ReceivedMessageBatch):
        super()._receiveMessageBatch(batch)

    def _bestMatchOf(self, user: User) -> Optional[User]:
        for test_user in self.database.matchCandidatesOf(user.id):
            return test_user

    def _messagesReadyToBeProcessed(self, messages: List[ReceivedMessage], from_user: User, to_user: User) -> bool:
        return True

    def _modifyUnsentMessages(self, messages: List[ReceivedMessage], from_user: User, to_user: User) -> List[ModifiedMessage]:
        return [ModifiedMessage(message.id, to_user.thread_id, message.content, message.timestamp) for message in messages]