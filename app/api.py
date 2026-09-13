from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from app.chatbot.engine import load_intents, get_response
from app.chatbot.conversation import ConversationState
from app.database.models import init_db, SessionLocal, User, Conversation, Message
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager

import logging
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level = logging.INFO)
logger = logging.getLogger("chatbot_api")


app = FastAPI(title="Student Assistant Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only - restrict this in production (Step 17)
    allow_methods=["*"],
    allow_headers=["*"],
)

intents = load_intents()

active_states: dict[int, ConversationState] = {}

class ChatRequest(BaseModel):
    conversation_id: int | None = None
    message: str = Field(..., min_length = 1, max_length = 500)

class ChatResponse(BaseModel):
    conversation_id: int
    reply: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

allowed_origins = os.environ.get("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app = FastAPI(title="Student Assistant Chatbot API", lifespan=lifespan)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/chat", response_model=ChatResponse)
@limiter.limit("10/minute")
def chat(request: Request, chat_request: ChatRequest):
    db = SessionLocal()

    if chat_request.conversation_id is None:
        user = User()
        db.add(user)
        db.commit()

        conversation = Conversation(user_id=user.id)
        db.add(conversation)
        db.commit()

        state = ConversationState()
        active_states[conversation.id] = state
    else:
        conversation_id = chat_request.conversation_id
        state = active_states.get(conversation_id, ConversationState())
        active_states[conversation_id] = state
        conversation = db.query(Conversation).filter_by(id=conversation_id).first()

        if conversation is None:
            db.close()
            return ChatResponse(conversation_id=conversation_id, reply="Error: conversation not found.")

    db.add(Message(conversation_id=conversation.id, sender="user", text=chat_request.message))
    db.commit()

    reply = get_response(chat_request.message, intents, state)
    logger.info(f"conversation_id={conversation.id} intent_matched=logged")

    if reply == "__EXIT__":
        reply = "Goodbye! Good luck with your studies."
        db.add(Message(conversation_id=conversation.id, sender="bot", text=reply, intent_tag="goodbye"))
    else:
        db.add(Message(conversation_id=conversation.id, sender="bot", text=reply))

    db.commit()
    conversation_id_value = conversation.id
    db.close()

    return ChatResponse(conversation_id=conversation_id_value, reply=reply)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log the FULL error internally for debugging...
    logger.error(f"Unhandled error on {request.url.path}: {exc}", exc_info=True)

    # ...but return a GENERIC message to the user - never expose internals
    return JSONResponse(
        status_code=500,
        content={"detail": "Something went wrong. Please try again later."}
    )

@app.post("/chat", response_model=ChatResponse)
@limiter.limit("10/minute")  # max 10 messages per minute per IP
def chat(request: Request, chat_request: ChatRequest):
    ...

@app.get("/")
def root():
    return {"status": "Student Assistant Chatbot API is running"}