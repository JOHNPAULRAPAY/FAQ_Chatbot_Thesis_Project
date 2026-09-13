from datetime import datetime, UTC
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key = True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    conversations = relationship("Conversation", back_populates = "user")

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key = True)
    user_id = Column(Integer, ForeignKey("users.id"))
    started_at = Column(DateTime, default=lambda: datetime.now(UTC))

    user = relationship("User", back_populates = "conversations")
    messages = relationship("Message", back_populates = "conversation")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key = True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    sender = Column(String, nullable = False)
    text = Column(String, nullable = False)
    intent_tag = Column(String, nullable = True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    conversation = relationship("Conversation", back_populates = "messages")
    feedback = relationship("Feedback", back_populates = "message")

class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key = True)
    message_id = Column(Integer, ForeignKey("messages.id"))
    rating = Column(String, nullable = False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    message = relationship("Message", back_populates = "feedback")
    
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///chatbot.db")
DATABASE_URL = "sqlite:///chatbot.db"

engine = create_engine(DATABASE_URL, echo = False)
SessionLocal = sessionmaker(bind = engine)

def init_db():
    Base.metadata.create_all(engine)