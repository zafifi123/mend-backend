from fastapi import APIRouter, Request
from pydantic import BaseModel
from llm.llm_client import generate_trade_explanation

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

@router.post("/")
async def chat(request: ChatRequest):
    reply = generate_trade_explanation(request.message)
    return {"response": reply}
