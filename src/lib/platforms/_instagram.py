from typing import List
from instagrapi import Client
from ...interface import ISocialPlatform, User, Message, MessageBatch


THREAD_FETCH_LIMIT = 40
THREAD_MSG_LIMIT = 20

class Instagram(ISocialPlatform):
    client: Client
    user_id: str

    def __init__(self, username: str, password: str):
        self.client = Client()
        self.client.login(username, password)
        self.user_id = self.client.user_id_from_username(username)
        # self.client.direct_messages(to_user_id, message)

    def sendMessage(self, to_user_id: str, message: str) -> bool:
        self.client.direct_threads()
        msg = self.client.direct_send(message, [int(to_user_id)])
        if msg.thread_id is not None:
            self.client.direct_send_seen(int(msg.thread_id))
        return True # fix to return whether message was successfully sent

    def getNewUsers(self) -> List[User]:
        '''
            get new users from new pending messages
            and approve their message requests, so
            they can be seen in the direct_threads
        '''
        users: List[User] = []
        threads = self.client.direct_pending_inbox()
        for thread in threads:
            if thread.id is not None:
                self.client.direct_pending_approve(int(thread.id))
            user_id = thread.messages[0].user_id
            if user_id is not None:
                user_info = thread.users[0]
                users.append(User(user_id, username=user_info.username, full_name=user_info.full_name))
        return users

    def getNewMessages(self) -> List[MessageBatch]:
        '''
            get new messages from all threads and mark them as seen
            Return: dictionary of thread_id -> list of messages,
            where messages should be sorted by timestamp
        '''
        message_batches: List[MessageBatch] = []
        threads = self.client.direct_threads(
            THREAD_FETCH_LIMIT,
            selected_filter="unread",
            thread_message_limit=THREAD_MSG_LIMIT
        )
        for thread in threads:
            user_id = thread.messages[0].user_id
            if user_id is None or thread.id is None:
                continue
            message_batch = MessageBatch(user_id, [])
            self.client.direct_send_seen(int(thread.id))
            for message in thread.messages:
                if message.user_id != user_id or message.text is  None:
                    continue
                message_batch.socialMessages.append(Message(message.id, user_id, message.text))
        return message_batches

    def getUser(self, user_id: str) -> User:
        user_info = self.client.user_info(user_id)
        return User(user_id, username=user_info.username, full_name=user_info.full_name)