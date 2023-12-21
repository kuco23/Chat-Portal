from typing import List
from abc import ABC
from dataclasses import dataclass

class ISocialPlatform(ABC):
    def sendMessage(self, to_user_id: str, message: str):
        raise NotImplementedError()

@dataclass
class SocialMessage:
    id: str
    from_user_id: str
    content: str

@dataclass
class SocialUser:
    id: str
    match_id: str | None
    last_message: SocialMessage | None

class IDatabase(ABC):

    def addUser(self, user_id: str) -> SocialUser:
        raise NotImplementedError()

    # replaces the old last_message with a new message
    def addMessage(self, to_user_id: str, message: SocialMessage):
        raise NotImplementedError()

    # matches a user with another user
    def matchUsers(self, user1_id: str, user2_id: str):
        raise NotImplementedError()

    # fetches a user from the database
    def findUser(self, user_id: str) -> SocialUser | None:
        raise NotImplementedError()

    # fetches all users that are candidates for matching with the given user
    def fetchMatchCandidates(self, user_id: str) -> List[SocialUser]:
        raise NotImplementedError()

class IMirroring(ABC):

    def initNewUser(self, user_id: str) -> SocialUser:
        raise NotImplementedError()

    def receiveMessage(self, message: SocialMessage):
        raise NotImplementedError()