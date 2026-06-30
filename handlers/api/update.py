from fastapi import APIRouter
from objects import glob

router = APIRouter()

php_file = True


@router.get("/")
async def send_update():
    data = {
        "version_code": glob.config.client_version_code,
        "link": glob.config.client_link,
        "changelog": glob.config.client_changelog,
    }
    return f"{data}"
