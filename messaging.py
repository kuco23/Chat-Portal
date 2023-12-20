from .entities import UserEntity

class Message:
    id: str
    content: str

class MessageService:

    def sendMessage(self, from_user_id: str, to_user_id: str, message: str):
        pass