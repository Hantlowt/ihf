import asyncio
import websockets
from ihf.Client import Client
from ihf.Session import SessionManager
from ihf.Template import open_template


async def update_property(obj, attr, function, *args, client=None, sleep=1):
    while True:
        setattr(obj, attr, function(*args))
        if client is not None:
            await client.send_render()
        await asyncio.sleep(sleep)


async def automatic_refresh(client, sleep=1):
    while True:
        await client.send_render()
        await asyncio.sleep(sleep)


class ihf:
    def __init__(self, app, template_name):
        self.app = app
        self.template = open_template(template_name)
        self.sessions_manager = SessionManager()

    async def parse(self, websocket, path):
        client = Client(websocket, self.template, self.app, self.sessions_manager)
        while True:
            try:
                await client.recv()
            except Exception as e:
                del client
                break

    def serve(self, host="localhost", port=8765, ssl_context=None):
        start_server = websockets.serve(self.parse, host, port, ssl=ssl_context)
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()
