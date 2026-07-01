from fastapi import APIRouter
from fastapi.responses import JSONResponse
from objects import glob

router = APIRouter()


@router.get("")
async def whitelist():
    maps = await glob.db.fetchall("SELECT * FROM maps WHERE status = 5")
    return JSONResponse(content=maps)
