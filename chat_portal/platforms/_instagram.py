from typing import Optional, List
from random import randint
from time import sleep
from instagrapi import Client
from instagrapi.types import DirectThread, DirectMessage
from ..interface import ISocialPlatform, User, Message
from .._models import MessageBatch


THREAD_FETCH_LIMIT = 20
THREAD_MSG_LIMIT = 20

class Instagram(ISocialPlatform):
    client: Client
    user_id: str

    def __init__(self, username: str, password: str):
        self.client = Client()
        self.client.login(username, password)
        self.user_id = self.client.user_id_from_username(username)

    def sendMessage(self, to_user: User, message: str) -> bool:
        self.client.direct_send_seen(int(to_user.thread_id))
        sleep(self._secondsToWaitForTypingText(message))
        self.client.direct_send(message, [int(to_user.id)])
        return True # fix to return whether message was successfully sent

    def getNewMessages(self) -> List[MessageBatch]:
        new_approved = self._getApprovedMessages(False)
        new_pending = self._getPendingMessages()
        return new_approved + new_pending

    def getOldMessages(self) -> List[MessageBatch]:
        return self._getApprovedMessages(True)

    def getUser(self, user_id: str) -> Optional[User]:
        user_info = self.client.user_info(user_id)
        resp = self.client.direct_thread_by_participants([int(user_id)])
        threads = resp.get('items')
        if threads is None or len(threads) == 0: return
        return User(user_id, threads[0].id, username=user_info.username, full_name=user_info.full_name)

    def _getApprovedMessages(self, old: bool) -> List[MessageBatch]:
        batches: List[MessageBatch] = []
        threads = self.client.direct_threads(THREAD_FETCH_LIMIT, "" if old else "unread", "", THREAD_MSG_LIMIT)
        for thread in threads:
            batch = self._threadToMessageBatch(thread, old)
            if batch is not None:
                batches.append(batch)
        return batches

    def _getPendingMessages(self) -> List[MessageBatch]:
        batches: List[MessageBatch] = []
        threads = self.client.direct_pending_inbox()
        for thread in threads:
            if thread.id is None: continue
            batch = self._threadToMessageBatch(thread, True)
            if batch is not None: batches.append(batch)
            self.client.direct_pending_approve(int(thread.id))
        return batches

    # if unanwered then return only messages that were sent without our user replying
    def _threadToMessageBatch(self, thread: DirectThread, unanswered: bool) -> Optional[MessageBatch]:
        user_id: Optional[str] = None
        messages: List[Message] = []
        for direct_message in thread.messages:
            if direct_message.user_id == self.user_id:
                if unanswered: break
                else: continue
            message = self._directMessageToMessage(direct_message)
            if message is not None:
                messages.append(message)
            if user_id is None:
                user_id = direct_message.user_id
        if user_id is None: return
        # user_info does not have an id for some reason, so we gotta get hacky
        # ideally we should check whether thread.users[0].username exists
        # if it does, we should check it matches self.user_id,
        # else we should fetch the user's info with self.getUser(user_id)
        user_info = thread.users[0]
        user = User(user_id, thread.id, username=user_info.username, full_name=user_info.full_name)
        return MessageBatch(user, messages)

    def _directMessageToMessage(self, message: DirectMessage) -> Optional[Message]:
        if message.user_id is None: return
        text = ""
        if message.text is not None:
            text += message.text
        elif message.xma_share is not None:
            text += str(message.xma_share.video_url)
        else: return
        return Message(message.id, message.user_id, text, message.timestamp.timestamp())

    @staticmethod
    def _secondsToWaitForTypingText(text: str) -> int:
        return randint(len(text) // 3, len(text) // 2)