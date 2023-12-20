from typing import List
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from .entities import UserEntity, MessageEntity
from .messaging import Message

DEFAULT_SQL_URL = "sqlite+pysqlite:///:memory:"

class Database:

    def __init__(self, db_url: str = DEFAULT_SQL_URL):
        self.engine = create_engine(db_url, echo=True)

    def addUser(self, user_id: str) -> UserEntity:
        with Session(self.engine) as session:
            user_entity = UserEntity(id=user_id)
            session.add(user_entity)
            session.commit()
            return user_entity

    def addMessage(self, from_user: UserEntity, to_user: UserEntity, message: Message):
        with Session(self.engine) as session:
            from_user.last_message = MessageEntity(
                id=message.id,
                content=message.content,
                from_user=from_user,
                to_user=to_user
            )
            session.add(from_user)
            session.commit()

    # matches a user with another user
    def matchUsers(self, user1: UserEntity, user2: UserEntity):
        with Session(self.engine) as session:
            user1.match = user2
            user2.match = user1
            session.add(user1)
            session.add(user2)
            session.commit()

    # fetches a user from the database
    def findUser(self, user_id: str) -> UserEntity | None:
        with Session(self.engine) as session:
            return session.query(UserEntity).filter(UserEntity.id == user_id).one_or_none()

    # fetches all users that are candidates for matching with the given user
    def fetchMatchCandidates(self, user: UserEntity) -> List[UserEntity]:
        with Session(self.engine) as session:
            return session.query(UserEntity).filter(UserEntity.id != user.id).all()
