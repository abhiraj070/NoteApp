from sqlalchemy import Column, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from ..db.database import Base


class Notes(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    user = relationship("User", back_populates="Notes")
