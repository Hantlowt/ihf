import asyncio
import websockets
import ihf
from ihf.Client import Client
from ihf.Session import SessionManager
from ihf.Template import open_template
from http import HTTPStatus
import functools
import os
import mimetypes

mimetypes.init()


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
    def __init__(self, app, template_name, host="localhost", port=8765, ssl_context=None):
        self.app = app
        self.template = open_template(template_name)
        self.sessions_manager = SessionManager()
        self.host = host
        self.port = port
        self.ssl_context = ssl_context

    async def process_request(self, sever_root, path, request_headers):
        """Serves a file when doing a GET request with a valid path."""

        if "Upgrade" in request_headers:
            return  # Probably a WebSocket connection

        if path == '/':
            path = '/index.html'

        response_headers = [
            ('Server', 'IHF Server'),
            ('Connection', 'close'),
        ]

        # Derive full system path
        full_path = os.path.realpath(os.path.join(sever_root + '/www', path[1:]))

        # Validate the path
        if os.path.commonpath((sever_root, full_path)) != sever_root or \
                not os.path.exists(full_path) or not os.path.isfile(full_path):
            full_path = os.path.dirname(__file__) + '/www/' + path[1:]
            if not os.path.isfile(full_path):
                print("HTTP GET {} 404 NOT FOUND".format(path))
                return HTTPStatus.NOT_FOUND, [], b'404 NOT FOUND'

        extension = full_path.split(".")[-1]
        mime_type = mimetypes.types_map.get('.'+extension, "application/octet-stream")
        response_headers.append(('Content-Type', mime_type))

        # Read the whole file into memory and send it out
        body = open(full_path, 'rb').read()
        if extension in ['html', 'htm']:
            body = bytes(str(body).replace('{host}', self.host).replace('{port}', str(self.port)), encoding='UTF-8')
        response_headers.append(('Content-Length', str(len(body))))
        print("HTTP GET {} 200 OK".format(path))
        return HTTPStatus.OK, response_headers, body

    async def parse(self, websocket, path):
        client = Client(websocket, self.template, self.app, self.sessions_manager)
        while True:
            try:
                await client.recv()
            except Exception as e:
                del client
                break

    def serve(self):
        handler = functools.partial(self.process_request, os.getcwd())
        start_server = websockets.serve(self.parse, self.host, self.port,
                                        ssl=self.ssl_context, process_request=handler)
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()
