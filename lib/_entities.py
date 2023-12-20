from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, relationship, Mapped, DeclarativeBase

class Base(DeclarativeBase):
    pass

class UserEntity(Base):
    __tablename__ = "user"

    id: Mapped[str] = mapped_column(primary_key=True)
    match_id = mapped_column(ForeignKey('user.id'), nullable=True) # nullable, because not every user can find a suitable match
    # relationships
    last_message = relationship("MessageEntity", back_populates="from_user", uselist=False)
    match = relationship("UserEntity", uselist=False, remote_side=[id])

class MessageEntity(Base):
    __tablename__ = "message"

    id: Mapped[str] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column()
    from_user_id = mapped_column(ForeignKey('user.id'))
    # relationships
    from_user = relationship("UserEntity", back_populates="last_message", foreign_keys=[from_user_id], uselist=False)