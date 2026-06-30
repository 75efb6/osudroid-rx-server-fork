from fastapi import APIRouter
import utils
from handlers.response import ApiResponse

router = APIRouter()


@router.get("/")
async def get_countries():
    countries = await utils.get_countries()
    return ApiResponse.ok([country for country in countries])
