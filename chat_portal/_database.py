from typing import List
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session
from sqlalchemy_utils import database_exists, create_database
from ._entities import Base, User, Thread, Message, ModifiedMessage, ReceivedMessage
from .interface import IDatabase


class Database(IDatabase):
    engine: Engine

    def __init__(self, db_url):
        self.engine = create_engine(db_url, echo=False)
        if not database_exists(db_url):
            create_database(db_url)
        Base.metadata.create_all(self.engine)

    def addEntities(self, entities: List[User] | List[ReceivedMessage] | List[ModifiedMessage] | List[Thread]):
        with Session(self.engine, expire_on_commit=False) as session:
            session.bulk_save_objects(entities)
            session.commit()

    ################################### fetching entities ######################################################

    def fetchUser(self, user_id: str):
        with Session(self.engine, expire_on_commit=False) as session:
            return session.query(User).filter(User.id == user_id).one_or_none()

    def fetchThread(self, thread_id: str):
        with Session(self.engine, expire_on_commit=False) as session:
            return session.query(Thread).filter(Thread.id == thread_id).one_or_none()

    def fetchReceivedMessage(self, message_id: str):
        with Session(self.engine, expire_on_commit=False) as session:
            return session.query(ReceivedMessage).filter(ReceivedMessage.id == message_id).one_or_none()

    def fetchModifiedMessage(self, message_id: str):
        with Session(self.engine, expire_on_commit=False) as session:
            return session.query(ModifiedMessage).filter(ModifiedMessage.id == message_id).one_or_none()

    def unprocessedMessagesOnThread(self, thread: Thread):
        with Session(self.engine, expire_on_commit=False) as session:
            return session.query(ReceivedMessage).filter(
                ReceivedMessage.thread_id == thread.id,
                ReceivedMessage.processed == False
            ).order_by(ReceivedMessage.timestamp.asc()).all()

    def unsentMessagesOnThread(self, thread: Thread):
        with Session(self.engine, expire_on_commit=False) as session:
            return session.query(ModifiedMessage).filter(
                ModifiedMessage.thread_id == thread.id,
                ModifiedMessage.sent == False
            ).order_by(ModifiedMessage.timestamp.asc()).all()

    def pairedThreads(self) -> List[Thread]:
        with Session(self.engine, expire_on_commit=False) as session:
            return session.query(Thread).filter(Thread.pair_id.is_not(None)).all()

    def pairCandidatesOf(self, user_id: str) -> List[Thread]:
        with Session(self.engine, expire_on_commit=False) as session:
            return session.query(Thread).filter(Thread.id != user_id, Thread.pair_id.is_(None)).all()

    ################################### updating entities ######################################################

    def markMessageProcessed(self, message: ReceivedMessage):
        with Session(self.engine, expire_on_commit=False) as session:
            message.processed = True
            session.add(message)
            session.commit()

    def markMessageSent(self, message: ModifiedMessage):
        with Session(self.engine, expire_on_commit=False) as session:
            message.sent = True
            session.add(message)
            session.commit()

    def pairThreads(self, thread_1: Thread, thread_2: Thread):
        with Session(self.engine, expire_on_commit=False) as session:
            thread_1.pair_id = thread_2.id
            thread_2.pair_id = thread_1.id
            session.add(thread_1)
            session.add(thread_2)
            session.commit()


    ################################### advanced ###############################################################

    def userFromThread(self, thread_id: str):
        with Session(self.engine, expire_on_commit=False) as session:
            thread = session.query(Thread).filter(Thread.id == thread_id).one_or_none()
            assert thread is not None, "Thread not found by passed id"
            return session.query(User).filter(User.id == thread.user_id).one_or_none()

    def conversationHistory(self, thread_id: str, before_timestamp: float, n_context_msg: int) -> List[Message]:
        with Session(self.engine, expire_on_commit=False) as session:
            messages = session.query(Message).filter(
                Message.thread_id == thread_id,
                Message.timestamp >= before_timestamp
            ).order_by(Message.timestamp.asc()).all()
            context = session.query(Message).filter(
                Message.thread_id == thread_id,
                Message.timestamp < before_timestamp
            ).order_by(
                Message.timestamp.desc()
            ).limit(n_context_msg).all()
            return context[::-1] + messages