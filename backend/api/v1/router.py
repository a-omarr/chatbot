from fastapi import APIRouter

from . import bot

api_router = APIRouter()

api_router.include_router(bot.router, prefix="/bot", tags=["bot"])
