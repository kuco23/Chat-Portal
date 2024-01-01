from typing import List
from dataclasses import dataclass
from ._entities import User, Message

@dataclass
class MessageBatch:
    from_user: str | User
    messages: List[Message]

    @property
    def from_user_id(self) -> str:
        if type(self.from_user) is str:
            return self.from_user
        elif type(self.from_user) is User:
            return self.from_user.id
        else:
            raise TypeError(f"MessageBatch: invalid sender type {type(self.from_user)}")