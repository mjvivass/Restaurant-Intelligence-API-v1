from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime
from app.db.session import Base


class Restaurant(Base):

    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    active = Column(Boolean, default=True)
