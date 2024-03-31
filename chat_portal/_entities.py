from random import randint
from hashlib import sha256
from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, relationship, Mapped, DeclarativeBase


class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(primary_key=True)
    # user info
    username: Mapped[str] = mapped_column(nullable=True)
    full_name: Mapped[str] = mapped_column(nullable=True)
    gender: Mapped[bool] = mapped_column(nullable=True)
    platform: Mapped[str] = mapped_column(nullable=True) # platform on which this user operates

    def __init__(self, id: str, **kwargs):
        super().__init__(id=id, **kwargs)

class Thread(Base):
    __tablename__ = "threads"
    # external ids
    id: Mapped[str] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    pair_id: Mapped[str] = mapped_column(ForeignKey('threads.id'), nullable=True, unique=True)
    # relationships
    pair: Mapped["Thread"] = relationship("Thread", remote_side=[id], uselist=False)

    def __init__(self, id: str, user_id: str, **kwargs):
        super().__init__(id=id, user_id=user_id, **kwargs)

class Message(Base):
    __tablename__ = "messages"
    # external ids
    id: Mapped[str] = mapped_column(primary_key=True)
    thread_id: Mapped[str] = mapped_column(ForeignKey('threads.id'))
    # message info
    content: Mapped[str] = mapped_column()
    timestamp: Mapped[float] = mapped_column()
    modified: Mapped[bool] = mapped_column()

class ReceivedMessage(Message):
    __tablename__ = "received_messages"
    id: Mapped[str] = mapped_column(ForeignKey("messages.id"), primary_key=True)
    processed: Mapped[bool] = mapped_column(default=False)

    def __init__(self, id: str, thread_id: str, content: str, timestamp: float, **kwargs):
        super().__init__(id=id, thread_id=thread_id, content=content,
            timestamp=timestamp, processed=False, modified=False, **kwargs)

class ModifiedMessage(Message):
    __tablename__ = "modified_messages"
    id: Mapped[str] = mapped_column(ForeignKey("messages.id"), primary_key=True)
    sent: Mapped[bool] = mapped_column(default=False)
    original_id: Mapped[str] = mapped_column(ForeignKey('received_messages.id'))

    def __init__(self, original_id: str, thread_id: str, content: str, timestamp: float, **kwargs):
        # ideally each modified message would have their own original_id
        id = sha256((original_id + str(randint(0, 2**32))).encode()).hexdigest()
        super().__init__(id=id, original_id=original_id, thread_id=thread_id,
            content=content, timestamp=timestamp, sent=False, modified=True, **kwargs)
