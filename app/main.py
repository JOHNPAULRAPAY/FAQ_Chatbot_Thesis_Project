from app.chatbot.engine import load_intents, get_response
from app.chatbot.conversation import ConversationState
from app.database.models import init_db, SessionLocal, User, Conversation, Message

def run_chatbot():
    init_db()
    db = SessionLocal()

    user = User()
    db.add(user)
    db.commit()

    conversation = Conversation(user_id = user.id)
    db.add(conversation)
    db.commit()

    intents = load_intents()
    state = ConversationState()

    print("=" * 50)
    print("Student Assistant Chatbot (type 'bye' to exit)")
    print("=" * 50)

    while True:
        user_input = input("You: ")

        if not user_input.strip():
            print("Bot: Please type something.")
            continue

        db.add(Message(conversation_id = conversation.id, sender = "user", text = user_input))
        db.commit()

        response = get_response(user_input, intents, state)

        if response == "__EXIT__":
            reply_text = "Goodbye! Good luck with your studies."
            db.add(Message(conversation_id=conversation.id, sender="bot", text=reply_text, intent_tag="goodbye"))
            db.commit()
            print(f"Bot: {reply_text}")
            break

        db.add(Message(conversation_id=conversation.id, sender="bot", text=response))
        db.commit()

        print(f"Bot: {response}")

    db.close()

if __name__ == "__main__":
    run_chatbot()