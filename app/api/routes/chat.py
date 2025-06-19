from fastapi import APIRouter
from api.models import ChatMessage

router = APIRouter()

mock_chat_history = [
    ChatMessage(message="Hello, how can I help you?"),
    ChatMessage(message="What is the outlook for AAPL?"),
    ChatMessage(message="AAPL is showing bullish momentum this week."),
]

@router.post("/chat", response_model=ChatMessage)
def send_chat_message(message: str):
    return ChatMessage(message=f"Mock AI response to: {message}")

@router.get("/chat/history", response_model=list[ChatMessage])
def get_chat_history():
    return mock_chat_history 