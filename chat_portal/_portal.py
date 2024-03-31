from typing import Optional, List, Tuple
from .interface import IPortal, ISocialPlatform, IDatabase
from ._models import ReceivedMessageBatch
from ._entities import User, Thread, ReceivedMessage, ModifiedMessage
from ._logger import logger


# assumes all messages fetched from database are ordered by timestamp

class AbstractPortal(IPortal):
    database: IDatabase
    social_platform: ISocialPlatform

    def runStep(self):
        self._forceForwardAllMessages()
        batches = self.social_platform.getNewMessages()
        self.receiveMessageBatches(batches)

    def jumpstart(self):
        logger.info("Portal: jumpstarting")
        batches = self.social_platform.getOldMessages()
        self.receiveMessageBatches(batches)

    def _receiveMessageBatches(self, batches: List[ReceivedMessageBatch]):
        for batch in batches:
            self.receiveMessageBatch(batch)

    # think before changing the order of the method's function calls
    def _receiveMessageBatch(self, batch: ReceivedMessageBatch):
        if len(batch.messages) == 0: return
        # redefine objects with the actual db entity!
        thread, user = self._fetchOrCreateThreadAndUserEntities(batch.thread, batch.user)
        # store new messages, so they are available in the next steps
        n_new_messages = self._storeNewReceivedMessages(batch.messages)
        if n_new_messages == 0: return
        logger.info(f"Portal: stored {n_new_messages} new received messages from user {user.id} on thread {thread.id}")
        pair, exists = self._getPairIfNewWithExistenceStatus(thread)
        # if thread cannot be paired, end here
        if not exists: return
        self._pushForwardMessagesOnThread(thread)
        # if pair's messages were processed before this user was available
        # (or pairing criteria was not symmetric) then force-forward pair's messages
        if pair is not None:
            logger.info(f"Portal: forwarding messages from newly paired thread {pair.id} to user {user.id}")
            self._pushForwardMessagesOnThread(pair)

    def _forceForwardAllMessages(self):
        for thread in self.database.pairedThreads():
            self._pushForwardMessagesOnThread(thread)

    def _pushForwardMessagesOnThread(self, thread: Thread):
        assert thread.pair_id is not None
        assert (pair := self.database.fetchThread(thread.pair_id)) is not None
        self._processReceivedMessages(thread, pair)
        self._forwardModifiedMessagesToThread(pair)

    def _processReceivedMessages(self, thread: Thread, pair: Thread):
        unprocessed_messages = self.database.unprocessedMessagesOnThread(thread)
        unprocessed_messages.sort(key=lambda msg: msg.timestamp)
        if len(unprocessed_messages) == 0: return
        if not self._messagesReadyToBeProcessed(unprocessed_messages, thread, pair): return
        logger.info(f"Portal: modifying {len(unprocessed_messages)} messages from thread {thread.id}")
        modified_messages = self._modifyUnsentMessages(unprocessed_messages, thread, pair)
        # store modified messages in database and mark unprocessed messages as processed
        logger.info(f"Portal: storing modified messages on thread {thread.id}")
        for unprocessed_message in unprocessed_messages:
            self.database.markMessageProcessed(unprocessed_message)
        self.database.addEntities(modified_messages)

    def _forwardModifiedMessagesToThread(self, thread: Thread):
        modified_messages = self.database.unsentMessagesOnThread(thread)
        for message in modified_messages:
            self.social_platform.sendMessage(thread, message.content)
            logger.info(f"Portal: forwarded message {message.id} to thread {thread.id}")
            self.database.markMessageSent(message)

    def _fetchOrCreateThreadAndUserEntities(self, _thread: Thread, _user: Optional[User] = None) -> Tuple[Thread, User]:
        user = self.database.fetchUser(_thread.user_id)
        if user is None:
            if _user is None:
                _user = self.social_platform.getUser(_thread.user_id)
            assert _user, "Could not initiate user from thread"
            self.database.addEntities([_user])
            assert (user := self.database.fetchUser(_user.id)) is not None
            logger.info(f"Portal: initialized new user {user.id}")
        thread = self.database.fetchThread(_thread.id)
        if thread is None:
            self.database.addEntities([_thread])
            assert (thread := self.database.fetchThread(_thread.id)) is not None
            logger.info(f"Portal: initialized new thread {thread.id}")
        return thread, user

    def _storeNewReceivedMessages(self, messages: List[ReceivedMessage]):
        # messages sent before the latest message that is stored in the database
        # will not be stored (to not to process messages before database genesis)
        message_stack = sorted(messages, key=lambda msg: -msg.timestamp)
        i = 0
        for message in message_stack:
            if self.database.fetchReceivedMessage(message.id) is not None: break
            i += 1
        if i > 0:
            self.database.addEntities(message_stack[:i])
        return i

    # tries to fetch the pair or create it and returns it if it's newly created,
    # along with a flag telling if the pair exists
    def _getPairIfNewWithExistenceStatus(self, thread: Thread) -> Tuple[Optional[Thread], bool]:
        if thread.pair_id is None:
            pair = self._bestPairOf(thread)
            if pair is not None:
                self.database.pairThreads(thread, pair) # thread entities are updated
                logger.info(f"Portal: assigned pair {pair.id} to thread {thread.id}")
                return pair, True
            else: # no pair possible => end here
                logger.info(f"Portal: could not assign a pair to thread {thread.id}")
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

    def __init__(self,
        database: IDatabase,
        social_platform: ISocialPlatform
    ):
        self.database = database
        self.social_platform = social_platform

    @exceptWrapper
    def jumpstart(self):
        super().jumpstart()

    @exceptWrapper
    def runStep(self):
        super().runStep()

    @exceptWrapper
    def receiveMessageBatches(self, batches: List[ReceivedMessageBatch]):
        super()._receiveMessageBatches(batches)

    @exceptWrapper
    def receiveMessageBatch(self, batch: ReceivedMessageBatch):
        super()._receiveMessageBatch(batch)

    def _bestPairOf(self, thread: Thread) -> Optional[Thread]:
        for test_pair in self.database.pairCandidatesOf(thread.id):
            return test_pair

    def _messagesReadyToBeProcessed(self, messages: List[ReceivedMessage], from_thread: Thread, to_thread: Thread) -> bool:
        return True

    def _modifyUnsentMessages(self, messages: List[ReceivedMessage], from_thread: Thread, to_thread: Thread) -> List[ModifiedMessage]:
        return [ModifiedMessage(message.id, to_thread.id, message.content, message.timestamp) for message in messages]