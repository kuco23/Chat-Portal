from typing import List
from ..interface import IPortal, ISocialPlatform, IDatabase
from ._models import MessageBatch
from ._entities import User, ProcessedMessage
from ._logger import logger


class Portal(IPortal):
    database: IDatabase
    social_platform: ISocialPlatform

    def __init__(
        self: "Portal",
        database: IDatabase,
        social_platform: ISocialPlatform
    ):
        self.database = database
        self.social_platform = social_platform

    def runStep(self):
        try:
            self._processUnsentMessages()
            batches = self.social_platform.getNewMessages()
            self._handleMessageBatches(batches)
        except Exception as e:
            logger.exception(f"Portal: exception occurred while running step: {e}")

    def jumpstart(self):
        batches = self.social_platform.getOldMessages()
        self._handleMessageBatches(batches)

    def _handleMessageBatches(self, batches: List[MessageBatch]):
        logger.info(f"Portal: received {len(batches)} message batches to handle")
        for batch in batches:
            logger.info(f"Portal: handling {len(batch)} length message batch from user {batch.from_user_id}")
            self._receiveMessageBatch(batch)
            logger.info(f"Portal: handled message batch from user {batch.from_user_id}")

    def _receiveMessageBatch(self, messages: MessageBatch) -> User | None:
        if len(messages) == 0: return
        user = self.database.fetchUser(messages.from_user_id)
        # if user is not in the database, then add them
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
        # note that messages sent before the latest message that is stored in the database
        # will not be stored (to not to process messages before database genesis)
        i: int = 0
        message_queue = sorted(messages, key=lambda msg: -msg.timestamp)
        for i, message in enumerate(message_queue):
            message_exists = self.database.fetchMessage(message.id) is not None
            if message_exists: break
        self.database.addMessages(message_queue[i:])
        # try to match the user with another
        if user.match_id is None:
            match = self._bestMatchOf(user)
            if match is not None:
                self.database.matchUsers(user.id, match.id)
                user.match_id = match.id
                match.match_id = user.id
                logger.info(f"Portal: assigned match {match.id} to user {user.id}")
                # if match's messages were processed before this user was available
                # (or matching was not symmetric) then force-forward match's messages
                # note that messages will not be double-sent because sending them
                # is logged in the database - todo: think of a solution
                logger.info(f"Portal: forward messages from match {match.id} to user {match.id}")
                self._processAndForwardMessagesFrom(match)
            else: # no match possible => end here
                logger.info(f"Portal: could not assign a match to user {user.id}")
                return
        # if match is available, then process the message and send to the match
        logger.info(f"Portal: forward messages from user {user.id} to match {user.match_id}")
        self._processAndForwardMessagesFrom(user)

    def _processAndForwardMessagesFrom(self, user: User):
        if user.match_id is None: return
        unsent_messages = self.database.unsentMessagesFrom(user)
        if len(unsent_messages) == 0: return
        logger.info(f"Portal: processing {len(unsent_messages)} messages to be sent from user {user.id} to user {user.match_id}")
        processed_messages = self._processMessageBatch(MessageBatch(user.id, unsent_messages), user.match_id)
        if len(processed_messages) != len(unsent_messages):
            return logger.error(f"Portal: processed messages length does not match the unprocessed ones")
        for original_message, processed_message in zip(unsent_messages, processed_messages):
            self.social_platform.sendMessage(user.match_id, processed_message.content)
            self.database.markMessageSent(original_message, user.match_id)
            self.database.addProcessedMessage(processed_message)
            logger.info(f"Portal: processed message {processed_message.id} sent to user {user.match_id}")

    def _processUnsentMessages(self):
        for user in self.database.fetchMatchedUsers():
            self._processAndForwardMessagesFrom(user)

    ############################## Methods to override ##############################

    # tries to find a match for the given user
    # it should fetch the messages of user and each match candidate from the database
    # and find the most conversation-compatible ones using some algorithm (e.g. AI)
    def _bestMatchOf(self, user: User) -> User | None:
        for test_user in self.database.fetchMatchCandidates(user.id):
            return test_user

    # processes the message sent to this.user before being forwarded to the sender's match
    # this is necessary, e.g. when this.user is a woman but sender and the match are men
    # e.g. the message is "how does a girl like you find herself on this app?"
    # the message forwarded to the match should be "how does a guy like you find himself on this app?"
    def _processMessageBatch(self, batch: MessageBatch, to_user_id: str) -> List[ProcessedMessage]:
        return [ProcessedMessage(message.id, message.content) for message in batch]