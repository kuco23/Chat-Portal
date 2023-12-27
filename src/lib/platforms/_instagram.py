from typing import List
from instagrapi import Client
from instagrapi.types import DirectThread
from ...interface import ISocialPlatform, User, Message
from .._models import MessageBatch


THREAD_FETCH_LIMIT = 40
THREAD_MSG_LIMIT = 20

class Instagram(ISocialPlatform):
    client: Client
    user_id: str

    def __init__(self, username: str, password: str):
        self.client = Client()
        self.client.login(username, password)
        self.user_id = self.client.user_id_from_username(username)

    def sendMessage(self, to_user_id: str, message: str) -> bool:
        self.client.direct_threads()
        msg = self.client.direct_send(message, [int(to_user_id)])
        if msg.thread_id is not None:
            self.client.direct_send_seen(int(msg.thread_id))
        return True # fix to return whether message was successfully sent

    def getNewMessages(self) -> List[MessageBatch]:
        new_approved = self._getApprovedMessages(False)
        new_pending = self._getPendingMessages()
        return new_approved + new_pending

    def getOldMessages(self) -> List[MessageBatch]:
        return self._getApprovedMessages(True)

    def getUser(self, user_id: str) -> User:
        user_info = self.client.user_info(user_id)
        return User(user_id, username=user_info.username, full_name=user_info.full_name)

    def _getApprovedMessages(self, old: bool) -> List[MessageBatch]:
        batches: List[MessageBatch] = []
        threads = self.client.direct_threads(THREAD_FETCH_LIMIT, "" if old else "unread", "", THREAD_MSG_LIMIT)
        for thread in threads:
            batch = self._threadToMessageBatch(thread)
            if batch is not None: batches.append(batch)
            self.client.direct_send_seen(int(thread.id))
        return batches

    def _getPendingMessages(self) -> List[MessageBatch]:
        batches: List[MessageBatch] = []
        threads = self.client.direct_pending_inbox()
        for thread in threads:
            if thread.id is None: continue
            batch = self._threadToMessageBatch(thread)
            if batch is not None: batches.append(batch)
            self.client.direct_pending_approve(int(thread.id))
        return batches

    def _threadToMessageBatch(self, thread: DirectThread) -> MessageBatch | None:
        user_id: str | None = None
        messages: List[Message] = []
        for message in thread.messages:
            if message.user_id == self.user_id or message.user_id is None or message.text is None: continue
            messages.append(Message(message.id, message.user_id, message.text, message.timestamp.timestamp()))
            if user_id is None: user_id = message.user_id
        if user_id is None: return None
        # user_info does not have an id for some reason, so we gotta get hacky
        # ideally we should check whether thread.users[0].username exists
        # if it does, we should check it matches self.user_id,
        # else we should fetch the user's info with self.getUser(user_id)
        user_info = thread.users[0]
        user = User(user_id, username=user_info.username, full_name=user_info.full_name)
        return MessageBatch(user, messages)