from typing import List
from dataclasses import dataclass
from ._entities import User, ReceivedMessage

@dataclass
class ReceivedMessageBatch:
    from_user: User
    messages: List[ReceivedMessage]