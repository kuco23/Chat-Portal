from typing import List
from dataclasses import dataclass
from ._entities import User, Message

@dataclass
class MessageBatch:
    from_user: User
    messages: List[Message]