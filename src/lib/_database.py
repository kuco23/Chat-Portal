from typing import List
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy_utils import database_exists, create_database
from ..interface import IDatabase
from ._entities import Base, User, Message, ProcessedMessage

class Database(IDatabase):

    def __init__(self, db_url):
        self.engine = create_engine(db_url, echo=False)
        if not database_exists(db_url):
            create_database(db_url)
        Base.metadata.create_all(self.engine)

    def addUsers(self, users: List[User]):
        with Session(self.engine, expire_on_commit=False) as session:
            session.bulk_save_objects(users)
            session.commit()

    def addMessage(self, message: Message, to_user_id: str | None):
        with Session(self.engine, expire_on_commit=False) as session:
            from_user = session.query(User).filter(User.id == message.from_user_id).one()
            from_user.last_message_id = message.id
            if to_user_id is not None:
                message.to_user_id = to_user_id
            session.add(message)
            session.add(from_user)
            session.commit()

    def markMessageSent(self, message: Message, to_user_id: str):
        with Session(self.engine, expire_on_commit=False) as session:
            from_user = session.query(User).filter(User.id == message.from_user_id).one()
            message.to_user_id = to_user_id
            from_user.last_message_id = message.id
            session.add(message)
            session.add(from_user)
            session.commit()

    def addProcessedMessage(self, message: ProcessedMessage):
        with Session(self.engine, expire_on_commit=False) as session:
            session.add(message)
            session.commit()

    def unsentMessagesFrom(self, user: User) -> List[Message]:
        with Session(self.engine, expire_on_commit=False) as session:
            return session.query(Message).filter(Message.from_user_id == user.id, Message.to_user_id.is_(None)).all()

    # matches a user with another user
    def matchUsers(self, user1_id: str, user2_id: str):
        with Session(self.engine, expire_on_commit=False) as session:
            user1 = session.query(User).filter(User.id == user1_id).one()
            user2 = session.query(User).filter(User.id == user2_id).one()
            user1.match_id = user2_id
            user2.match_id = user1_id
            session.add(user1)
            session.add(user2)
            session.commit()

    # fetches a user from the database
    def findUser(self, user_id: str) -> User | None:
        with Session(self.engine, expire_on_commit=False) as session:
            return session.query(User).filter(User.id == user_id).one_or_none()

    # fetches all users that are candidates for matching with the given user
    def fetchMatchCandidates(self, user_id: str) -> List[User]:
        with Session(self.engine, expire_on_commit=False) as session:
            return session.query(User).filter(User.id != user_id, User.match_id.is_(None)).all()