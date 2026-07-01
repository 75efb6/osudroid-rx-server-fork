from fastapi import APIRouter
from objects import glob
from handlers.response import ApiResponse

router = APIRouter()


@router.get("")
async def get_online():
    online_players = [_ for _ in glob.players if _.online]
    return ApiResponse.ok(len(online_players))
