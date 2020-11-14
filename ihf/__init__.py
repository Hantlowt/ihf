import asyncio
import websockets
from ihf.Client import Client
from ihf.Session import SessionManager
from ihf.Template import open_template
from ihf.HttpProcess import HttpProcess
from ihf.File import FileManager
import functools
import os


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


class Ihf:
    def __init__(self, app, template_name, host="localhost", port=8765, ssl_context=None, loading_indicator=True):
        self.app = app
        self.template = open_template(template_name)
        if loading_indicator:
            self.template = '<link rel="stylesheet" href="loading.css"><div class="loading" style="display: None"></div>' + self.template
        self.sessions_manager = SessionManager()
        self.host = host
        self.port = port
        self.full_url = f'http://{self.host}{":" + str(self.port) if self.port != 80 else ""}'
        self.ssl_context = ssl_context
        self.httpProcess = HttpProcess(self.host, self.port, os.path.dirname(__file__) + '/www')
        self.file_manager = FileManager(self.full_url, os.getcwd() + '/www')

    async def parse(self, websocket, path):
        client = Client(websocket, self.template, self.app, self.sessions_manager, self.file_manager)
        while True:
            try:
                await client.recv()
            except Exception as e:
                del client
                break

    def serve(self, max_size=int(5e+7)):
        handler = functools.partial(self.httpProcess.process_request, os.getcwd())
        start_server = websockets.serve(self.parse, self.host, self.port,
                                        ssl=self.ssl_context, process_request=handler, max_size=max_size)
        print(f'SERVER RUNNING ON {self.full_url}')
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()
