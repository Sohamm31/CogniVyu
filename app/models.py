from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.sql import func
import uuid

from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(255))
    is_verified = Column(Boolean, default=False)



class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    
    conversation_id = Column(String(36), index=True, nullable=False)
    
    user_id = Column(Integer, ForeignKey("users.id"))
    human_message = Column(String(1000))
    bot_message = Column(String(4000))
    domain = Column(String(100))
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
