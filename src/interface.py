from typing import Optional, List
from abc import ABC, abstractmethod
from .lib._models import MessageBatch
from .lib._entities import User, Message, ProcessedMessage


class ISocialPlatform(ABC):

    @abstractmethod
    def sendMessage(self, to_user: User, message: str) -> bool: pass

    @abstractmethod
    def getNewMessages(self) -> List[MessageBatch]: pass

    @abstractmethod
    def getOldMessages(self) -> List[MessageBatch]: pass

    # gets user with full info (like username, full_name, gender)
    @abstractmethod
    def getUser(self, user_id: str) -> Optional[User]: pass

class IDatabase(ABC):

    @abstractmethod
    def addUsers(self, users: List[User]): pass

    @abstractmethod
    def addMessages(self, messages: List[Message]): pass

    # fetches a user from the database
    @abstractmethod
    def fetchUser(self, user_id: str) -> Optional[User]: pass

    @abstractmethod
    def fetchMessage(self, message_id: str) -> Optional[Message]: pass

    # matches a user with another user
    @abstractmethod
    def matchUsers(self, user1: User, user2: User): pass

    # fetches all users that are candidates for matching with the given user
    @abstractmethod
    def fetchMatchCandidates(self, user_id: str) -> List[User]: pass

    # fetches all users that have a match from the database
    @abstractmethod
    def fetchMatchedUsers(self) -> List[User]: pass

    # marks message sent by setting the to_user_id
    @abstractmethod
    def markMessageSent(self, message: Message, to_user: User): pass

    # returns all unsent messages from the given user
    @abstractmethod
    def unsentMessagesFrom(self, user: User) -> List[Message]: pass

    # adds a message processed by the given processor
    @abstractmethod
    def addProcessedMessage(self, message: ProcessedMessage): pass

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
    def _processMessageBatch(self, batch: MessageBatch, to_user: User) -> List[ProcessedMessage]: pass