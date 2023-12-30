from typing import List
from abc import ABC, abstractmethod
from .lib._models import MessageBatch
from .lib._entities import User, Message, ProcessedMessage


class ISocialPlatform(ABC):

    @abstractmethod
    def sendMessage(self, to_user_id: str, message: str) -> bool: pass

    @abstractmethod
    def getNewMessages(self) -> List[MessageBatch]: pass

    @abstractmethod
    def getOldMessages(self) -> List[MessageBatch]: pass

    # gets user with full info (like username, full_name, gender)
    @abstractmethod
    def getUser(self, user_id: str) -> User: pass

class IDatabase(ABC):

    @abstractmethod
    def addUsers(self, users: List[User]): pass

    @abstractmethod
    def addMessages(self, messages: List[Message]): pass

    # fetches a user from the database
    @abstractmethod
    def fetchUser(self, user_id: str) -> User | None: pass

    @abstractmethod
    def fetchMessage(self, message_id: str) -> Message | None: pass

    # matches a user with another user
    @abstractmethod
    def matchUsers(self, user1_id: str, user2_id: str): pass

    # fetches all users that are candidates for matching with the given user
    @abstractmethod
    def fetchMatchCandidates(self, user_id: str) -> List[User]: pass

    # fetches all users that have a match from the database
    @abstractmethod
    def fetchMatchedUsers(self) -> List[User]: pass

    # marks message sent by setting the to_user_id
    @abstractmethod
    def markMessageSent(self, message: Message, to_user_id: str): pass

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