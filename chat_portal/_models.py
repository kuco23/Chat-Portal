from typing import List, Optional
from dataclasses import dataclass
from ._entities import User, Thread, ReceivedMessage

@dataclass
class ReceivedMessageBatch:
    messages: List[ReceivedMessage]
    thread: Thread
    user: Optional[User]

    def __init__(self, messages: List[ReceivedMessage], thread: Thread, user: Optional[User] = None):
        self.messages = messages
        self.thread = thread
        self.user = user