import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.v1.bot import ChatRequest, ChatResponse
from api.v1.router import api_router
from app.services.bot_service import bot_service

logger = logging.getLogger("chatbot.api")

app = FastAPI(
    title="Chatbot API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration – adjust allowed origins for production
origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    return {"status": "ok"}


@app.post("/api/bot", response_model=ChatResponse, tags=["bot"])
async def chat_bot(request: ChatRequest) -> ChatResponse:
    """Bot endpoint at /api/bot.

    Accepts a JSON body with a `message` field and returns a reply.
    Includes basic error handling and logging.
    """
    try:
        if not request.message.strip():
            logger.warning("Received empty message payload")
            raise HTTPException(status_code=400, detail="Message must not be empty.")

        logger.info("Received bot request", extra={"message": request.message})

        # Delegate to service layer
        reply_text = bot_service.generate_reply(request.message)

        logger.info("Sending bot response", extra={"reply": reply_text})
        return ChatResponse(reply=reply_text)
    except HTTPException:
        # Let FastAPI handle HTTP errors we raised intentionally
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unhandled error in /api/bot")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing the request.",
        ) from exc


app.include_router(api_router, prefix="/api/v1")
