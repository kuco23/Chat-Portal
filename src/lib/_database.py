from typing import List
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy_utils import database_exists, create_database
from .interface import IDatabase, SocialUser, SocialMessage
from ._entities import Base, UserEntity, MessageEntity

class Database(IDatabase):

    def __init__(self, db_url):
        self.engine = create_engine(db_url, echo=False)
        if not database_exists(db_url):
            create_database(db_url)
        Base.metadata.create_all(self.engine)

    def addUser(self, user: SocialUser):
        with Session(self.engine) as session:
            userEntity = UserEntity(social_id=user.id, username=user.username, full_name=user.full_name, gender=user.gender)
            session.add(userEntity)
            session.commit()

    def addMessage(self, to_user_id: str, message: SocialMessage):
        with Session(self.engine) as session:
            # delete message if present, because sqlalchemy doesn't know how to replace a one-to-one child
            from_user = session.query(UserEntity).filter(UserEntity.social_id == message.from_user_id).one()
            if from_user.last_message is not None:
                session.delete(from_user.last_message)
            session.commit()
            last_message = MessageEntity(
                social_id=message.id,
                content=message.content,
                from_user_id=from_user.id,
                to_user_id=to_user_id
            )
            from_user.last_message = last_message
            session.add(last_message)
            session.add(from_user)
            session.commit()

    # matches a user with another user
    def matchUsers(self, user1_id: str, user2_id: str):
        with Session(self.engine) as session:
            user1 = session.query(UserEntity).filter(UserEntity.social_id == user1_id).one()
            user2 = session.query(UserEntity).filter(UserEntity.social_id == user2_id).one()
            user1.match_id = user2_id
            user2.match_id = user1_id
            session.add(user1)
            session.add(user2)
            session.commit()

    # fetches a user from the database
    def findUser(self, user_id: str) -> SocialUser | None:
        with Session(self.engine) as session:
            user = session.query(UserEntity).filter(UserEntity.social_id == user_id).one_or_none()
            if user is not None:
                return self._userEntityToObject(user)

    # fetches all users that are candidates for matching with the given user
    def fetchMatchCandidates(self, user_id: str) -> List[SocialUser]:
        with Session(self.engine) as session:
            users = session.query(UserEntity).filter(UserEntity.social_id != user_id, UserEntity.match_id.is_(None)).all()
            return [self._userEntityToObject(user) for user in users]

    @staticmethod
    def _userEntityToObject(user_entity: UserEntity) -> SocialUser:
        last_message = None
        if user_entity.last_message is not None:
            last_message = SocialMessage(
                user_entity.last_message.social_id,
                user_entity.last_message.from_user_id,
                user_entity.last_message.content
            )
        return SocialUser(
            user_entity.social_id,
            user_entity.username,
            user_entity.full_name,
            user_entity.gender,
            user_entity.match_id,
            last_message
        )

    @staticmethod
    def _messageEntityToObject(message_entity: MessageEntity) -> SocialMessage:
        return SocialMessage(message_entity.social_id, message_entity.from_user_id, message_entity.content)