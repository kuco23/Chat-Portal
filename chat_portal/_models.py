from typing import List
from dataclasses import dataclass
from ._entities import User, ReceivedMessage, ModifiedMessage

@dataclass
class ReceivedMessageBatch:
    from_user: User
    messages: List[ReceivedMessage]