from typing import List
from dataclasses import dataclass
from ._entities import User, Message

@dataclass
class MessageBatch:
    from_user: str | User
    messages: List[Message]

    def __iter__(self):
        return iter(self.messages)

    def __getitem__(self, i):
        return self.messages.__getitem__(i)

    def __len__(self):
        return self.messages.__len__()

    @property
    def from_user_id(self) -> str:
        if type(self.from_user) is str:
            return self.from_user
        elif type(self.from_user) is User:
            return self.from_user.id
        else:
            raise TypeError(f"MessageBatch: invalid sender type {type(self.from_user)}")