from instagrapi import Client
from ..interface import ISocialPlatform


class Instagram(ISocialPlatform):
    client: Client
    user_id: str
    medias: list

    def __init__(self, username: str, password: str):
        self.client = Client()
        self.client.login(username, password)
        self.user_id = self.client.user_id_from_username(username)
        # self.medias = self.client.user_medias(self.user_id, 20)
        # self.client.direct_messages(to_user_id, message)

    def sendMessage(self, to_user_id: str, message: str):
        self.client.direct_threads()
        msg = self.client.direct_send(message, [int(to_user_id)])
        if msg.thread_id is not None:
            self.client.direct_send_seen(int(msg.thread_id))
