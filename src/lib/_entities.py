from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, relationship, Mapped, DeclarativeBase

class Base(DeclarativeBase):
    pass

class UserEntity(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    social_id: Mapped[str] = mapped_column(unique=True)
    match_id: Mapped[str] = mapped_column(ForeignKey('user.id'), nullable=True)
    # relationships
    last_message: Mapped["MessageEntity"] = relationship("MessageEntity", back_populates="from_user", uselist=False)
    match: Mapped["UserEntity"] = relationship("UserEntity", remote_side=[id], uselist=False)

class MessageEntity(Base):
    __tablename__ = "message"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    social_id: Mapped[str] = mapped_column(unique=True)
    content: Mapped[str] = mapped_column()
    from_user_id: Mapped[str] = mapped_column(ForeignKey('user.id'))
    to_user_id: Mapped[str] = mapped_column()
    # relationships
    from_user: Mapped["UserEntity"] = relationship("UserEntity", back_populates="last_message")
