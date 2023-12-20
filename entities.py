from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, relationship, Mapped, DeclarativeBase

class Base(DeclarativeBase):
    pass

class UserEntity(Base):
    __tablename__ = "user"

    id: Mapped[str] = mapped_column(primary_key=True)
    last_message_id = mapped_column(ForeignKey('message.id'), nullable=True)
    last_message: Mapped["MessageEntity"] = relationship(back_populates="from_user")
    # matches are optional because adding a match instantly doesn't leave much freedom
    match_id = mapped_column(ForeignKey('user.id'), nullable=True)
    match: Mapped["UserEntity"] = relationship()

class MessageEntity(Base):
    __tablename__ = "message"

    id: Mapped[str] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column()
    from_user_id = mapped_column(ForeignKey('user.id'))
    from_user: Mapped[UserEntity] = relationship(back_populates="last_message")
    to_user_id = mapped_column(ForeignKey('user.id'))
    to_user: Mapped[UserEntity] = relationship()