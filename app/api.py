"""
FastAPI application: exposes the chatbot over HTTP.
"""
import logging
import os

from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.chatbot.engine import load_intents, get_response
from app.chatbot.conversation import ConversationState
from app.database.models import init_db, SessionLocal, User, Conversation, Message

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chatbot_api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Student Assistant Chatbot API", lifespan=lifespan)

# --- CORS: only one middleware block, using the env var ---
allowed_origins = os.environ.get("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Rate limiting ---
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

intents = load_intents()
active_states: dict[int, ConversationState] = {}


class ChatRequest(BaseModel):
    conversation_id: int | None = None
    message: str = Field(..., min_length=1, max_length=500)


class ChatResponse(BaseModel):
    conversation_id: int
    reply: str


# --- The ONE and only /chat route ---
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
    logger.error(f"Unhandled error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Something went wrong. Please try again later."}
    )


@app.get("/")
def root():
    return {"status": "Student Assistant Chatbot API is running"}