class Message:
    id: str
    content: str

    def __init__(self, id: str, content: str):
        self.id = id
        self.content = content

class User:
    id: str
    match_id: str | None
    last_message: Message | None

    def __init__(self, id: str, match_id: str | None = None, last_message: Message | None = None):
        self.id = id
        self.match_id = match_id
        self.last_message = last_message