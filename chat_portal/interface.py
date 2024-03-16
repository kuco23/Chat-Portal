from typing import Optional, List
from abc import ABC, abstractmethod
from ._models import ReceivedMessageBatch
from ._entities import User, Message, ReceivedMessage, ModifiedMessage


class ISocialPlatform(ABC):

    @abstractmethod
    def sendMessage(self, to_user: User, message: str) -> bool: pass

    @abstractmethod
    def getNewMessages(self) -> List[ReceivedMessageBatch]: pass

    @abstractmethod
    def getOldMessages(self) -> List[ReceivedMessageBatch]: pass

    # gets user with full info (like username, full_name, gender)
    @abstractmethod
    def getUser(self, user_id: str) -> Optional[User]: pass

class IDatabase(ABC):

    @abstractmethod
    def addEntities(self, entities: List[User] | List[ReceivedMessage] | List[ModifiedMessage]): pass

    # fetches a user from the database
    @abstractmethod
    def fetchUser(self, user_id: str) -> Optional[User]: pass

    @abstractmethod
    def fetchReceivedMessage(self, message_id: str) -> Optional[ReceivedMessage]: pass

    @abstractmethod
    def fetchModifiedMessage(self, message_id: str) -> Optional[ModifiedMessage]: pass

    # returns all unprocessed received messages from the given user
    @abstractmethod
    def unprocessedMessagesFrom(self, user: User) -> List[ReceivedMessage]: pass

    # returns all messages that were not yet sent to user
    @abstractmethod
    def unsentMessagesTo(self, to: User) -> List[ModifiedMessage]: pass

    # marks message processed
    @abstractmethod
    def markMessageProcessed(self, message: ReceivedMessage): pass

    @abstractmethod
    def markMessageSent(self, message: ModifiedMessage): pass

    # matches a user with another user
    @abstractmethod
    def matchUsers(self, user1: User, user2: User): pass

    # fetches all users that are candidates for matching with the given user
    @abstractmethod
    def matchCandidatesOf(self, user_id: str) -> List[User]: pass

    # fetches all users that have a match from the database
    @abstractmethod
    def matchedUsers(self) -> List[User]: pass

    # fetches user from thread id
    @abstractmethod
    def userFromThread(self, thread_id: str) -> Optional[User]: pass

    # returns the history of the unseen conversation + some additional context messages
    # needed for additional context when modifying received messages to ai
    @abstractmethod
    def conversationHistory(self, thread_id: str, before_timestamp: float, n_context_msg: int) -> List[Message]: pass


class IPortal(ABC):

    # runs a step by using social platform's new users and messages
    @abstractmethod
    def runStep(self): pass

    # jumpstarts the portal by using social platform's all users and messages
    @abstractmethod
    def jumpstart(self): pass

    ############################## Methods to override ##############################

    # tries to find a match for the given user
    # it should fetch the messages of user and each match candidate from the database
    # and find the most conversation-compatible ones using some algorithm (e.g. AI)
    @abstractmethod
    def _bestMatchOf(self, user: User) -> Optional[User]: pass

    # processes the message sent to this.user before being forwarded to the sender's match
    # this is necessary, e.g. when this.user is a woman but sender and the match are men
    # e.g. the message is "how does a girl like you find herself on this app?"
    # the message forwarded to the match should be "how does a guy like you find himself on this app?"
    @abstractmethod
    def _modifyUnsentMessages(self, messages: List[ReceivedMessage], from_user: User, to_user) -> List[ModifiedMessage]: pass

    # decides whether the messages are ready to be processed / modified
    # this can be useful when waiting for additional context when receiving messages
    @abstractmethod
    def _messagesReadyToBeProcessed(self, messages: List[ReceivedMessage], from_user: User, to_user: User) -> bool: pass