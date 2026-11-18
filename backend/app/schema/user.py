from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from ..db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    username = Column(String, nullable=False, unique=True, index=True)
    # Store a password hash here when authentication is implemented.
    password = Column(String, nullable=False)
    refreshtoken = Column(String, nullable=True)

    Notes = relationship("Notes", back_populates="user", cascade="all, delete-orphan")
