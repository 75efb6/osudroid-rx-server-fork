from quart import Blueprint
from objects import glob

bp = Blueprint("banner", __name__)

force_route = "/api/game/banner.php"

@bp.route("/")
async def send_banner():
    data = {
        "Url": glob.config.banner_url,
        "ImageLink": f"{glob.config.host}/static/banner.png",
    }
    return data
