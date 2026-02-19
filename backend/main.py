import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.v1.chat_router import ChatRequest, ChatResponse
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


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", tags=["system"])
async def health_check() -> dict:
    """Basic health check endpoint."""
    return {"status": "operational", "version": "1.0.0"}


@app.post("/api/bot", response_model=ChatResponse, tags=["chat"])
async def legacy_chat_bot(request: ChatRequest) -> ChatResponse:
    """Legacy chat endpoint for backward compatibility.
    
    Delegates to the bot_service logic.
    """
    try:
        if not request.message.strip():
            logger.warning("Received empty message")
            raise HTTPException(status_code=400, detail="Message cannot be empty.")

        # Logic delegated to service layer
        reply_text = bot_service.generate_reply(request.message)
        return ChatResponse(reply=reply_text)

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Internal error in legacy bot endpoint")
        raise HTTPException(
            status_code=500,
            detail="An internal server error occurred."
        ) from exc


# Include versioned API routers
app.include_router(api_router, prefix="/api/v1")
