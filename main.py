import os
import logging
import asyncio
import coloredlogs
from quart import Quart, render_template_string
import aiohttp
from handlers.multi import sio  # Import the socketio server
from socketio import ASGIApp
import ssl
import hypercorn.asyncio
# Other imports
from objects import glob
from objects.player import Player
from objects.db import PostgresDB
from handlers import (cho, api, user, multi)
from handlers.response import Failed
import utils
import html_templates


def make_app():
    app = Quart(__name__)

    # Register existing routes
    routes = [cho, api, user, multi]
    for route in routes:
        app.register_blueprint(route, url_prefix=route.prefix)

    return app


app = make_app()

@app.before_serving
async def init_shit():
    utils.check_folder()
    await glob.db.connect()

    # Initialize players
    player_ids = await glob.db.fetchall("SELECT id FROM users WHERE id != -1")
    for player_id in player_ids:
        player = await Player.from_sql(player_id['id'])
        glob.players.add(player)

    async def background_tasks():
        while True:
            try:
                for player in glob.players:
                    await player.update_stats()
            except Exception as err:
                logging.error(f'Failed to complete task: {repr(err)}')
            await asyncio.sleep(glob.config.cron_delay * 60)
                
    asyncio.create_task(background_tasks())

@app.after_serving
async def close_shit():
    await glob.db.close()

@app.errorhandler(500)
async def server_fucked(err):
    return Failed(f'Server Error: {repr(err)}')

@app.route('/')
async def index():
    players = len(glob.players)
    online = len([_ for _ in glob.players if _.online])
    title = 'odrx server'
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://{glob.config.ip}:{glob.config.port}/api/update.php") as resp:
            update = await resp.json()
            changelog = update['changelog']
            version = update['version_code']
            download_link = update['link']

    return await render_template_string(
        html_templates.main_page, players=players, online=online, title=title, changelog=changelog,
        download_link=download_link, version=version
    )


if __name__ == '__main__':
    coloredlogs.install(level=logging.DEBUG)

    app_asgi = ASGIApp(sio, app)
    hypercorn_config = hypercorn.Config()

    if os.path.exists(f"./certs/live/{glob.config.host}"):
        certfile = os.path.join(f'./certs/live/{glob.config.host}/fullchain.pem')
        keyfile = os.path.join(f'./certs/live/{glob.config.host}/privkey.pem')
        hypercorn_config.bind = [f"0.0.0.0:443"]
        hypercorn_config.keyfile = keyfile
        hypercorn_config.certfile = certfile
    else:
        hypercorn_config.bind = [f"{glob.config.ip}:{glob.config.port}"]

    asyncio.run(hypercorn.asyncio.serve(app_asgi, hypercorn_config))