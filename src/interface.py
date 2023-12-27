from typing import List
from abc import ABC
from dataclasses import dataclass
from .lib._entities import User, Message, ProcessedMessage


@dataclass
class MessageBatch:
    from_user_id: str
    socialMessages: List[Message]

    def __iter__(self):
        return iter(self.socialMessages)

    def __getitem__(self, i):
        return self.socialMessages.__getitem__(i)

    def __len__(self):
        return self.socialMessages.__len__()

class ISocialPlatform(ABC):

    def sendMessage(self, to_user_id: str, message: str) -> bool:
        raise NotImplementedError()

    def getNewUsers(self) -> List[User]:
        raise NotImplementedError()

    def getNewMessages(self) -> List[MessageBatch]:
        raise NotImplementedError()

    def getUser(self, user_id: str) -> User:
        raise NotImplementedError()

class IDatabase(ABC):

    def addUsers(self, users: List[User]):
        raise NotImplementedError()

    # matches a user with another user
    def matchUsers(self, user1_id: str, user2_id: str):
        raise NotImplementedError()

    # fetches a user from the database
    def findUser(self, user_id: str) -> User | None:
        raise NotImplementedError()

    # fetches all users that are candidates for matching with the given user
    def fetchMatchCandidates(self, user_id: str) -> List[User]:
        raise NotImplementedError()

    # replaces the old last_message with a new message
    def addMessage(self, message: Message, to_user_id: str | None):
        raise NotImplementedError()

    # marks message sent by setting the to_user_id
    def markMessageSent(self, message: Message, to_user_id: str):
        raise NotImplementedError()

    # returns all unsent messages from the given user
    def unsentMessagesFrom(self, user: User) -> List[Message]:
        raise NotImplementedError()

    # adds a message processed by the given processor
    def addProcessedMessage(self, message: ProcessedMessage):
        raise NotImplementedError()

class IPortal(ABC):

    def runStep(self) -> User:
        raise NotImplementedError()