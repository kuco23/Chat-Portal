from typing import List
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy_utils import database_exists, create_database
from ._objects import Message, User
from ._entities import Base, UserEntity, MessageEntity

DEFAULT_SQL_URL = "sqlite+pysqlite:///:memory:"

class Database:

    def __init__(self, db_url: str = DEFAULT_SQL_URL):
        self.engine = create_engine(db_url, echo=True)
        if not database_exists(db_url):
            create_database(db_url)
        Base.metadata.create_all(self.engine)

    def addUser(self, user_id: str) -> User:
        with Session(self.engine) as session:
            user = UserEntity(id=user_id)
            session.add(user)
            session.commit()
            return self._userEntityToObject(user)

    def addMessage(self, from_user_id: str, message: Message):
        with Session(self.engine) as session:
            from_user = session.query(UserEntity).filter(UserEntity.id == from_user_id).one()
            session.add(from_user)
            from_user.last_message = MessageEntity(
                id=message.id,
                content=message.content,
                from_user=from_user
            )
            session.commit()

    # matches a user with another user
    def matchUsers(self, user1_id: str, user2_id: str):
        with Session(self.engine) as session:
            user1 = session.query(UserEntity).filter(UserEntity.id == user1_id).one()
            user2 = session.query(UserEntity).filter(UserEntity.id == user2_id).one()
            session.add(user1)
            session.add(user2)
            user1.match = user2
            session.commit()

    # fetches a user from the database
    def findUser(self, user_id: str) -> User | None:
        with Session(self.engine) as session:
            user = session.query(UserEntity).filter(UserEntity.id == user_id).one_or_none()
            if user is not None:
                return self._userEntityToObject(user)

    # fetches all users that are candidates for matching with the given user
    def fetchMatchCandidates(self, user_id: str) -> List[User]:
        with Session(self.engine) as session:
            users = session.query(UserEntity).filter(UserEntity.id != user_id).all()
            return [self._userEntityToObject(user) for user in users]

    @staticmethod
    def _userEntityToObject(user_entity: UserEntity) -> User:
        last_message = None
        if user_entity.last_message is not None:
            last_message = Message(user_entity.last_message.id, user_entity.last_message.content)
        return User(user_entity.id, user_entity.match_id, last_message)

    @staticmethod
    def _messageEntityToObject(message_entity: MessageEntity) -> Message:
        return Message(message_entity.id, message_entity.content)