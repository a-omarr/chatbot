from fastapi import APIRouter
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Basic echo-style chatbot endpoint.

    Replace this with your actual model/integration later.
    """
    reply_text = f"You said: {request.message}"
    return ChatResponse(reply=reply_text)
