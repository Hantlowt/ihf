import asyncio
import websockets
import json


def rgetattr(obj, attr=None):
    value = obj
    if type(attr) == str and hasattr(obj, '__dict__'):
        value = getattr(obj, attr)
    if type(value) == Client:
        return None
    if isinstance(value, list):
        return [rgetattr(i) for i in value]
    if isinstance(value, dict):
        return {i: rgetattr(i) for i in value.keys() if not i.startswith('__')}
    if hasattr(value, '__dict__'):
        return {i: rgetattr(value, i) for i in vars(value).keys() if not i.startswith('_')}
    return value


class Client():
    def __init__(self, websocket, template, app):
        self.websocket = websocket
        self.template = template
        self.app = app(self)
        self.firstRun = True

    async def send_render(self):
        data = rgetattr(self.app)
        print(data)
        if self.firstRun:
            data['template'] = self.template
        data = json.dumps(data)
        await self.websocket.send(str(data))

    async def recv(self):
        message = await self.websocket.recv()
        try:
            message = eval(message)
            print(message)
            if not message[0].startswith('__') and message[0] in dir(self.app):
                f = getattr(self.app, message[0])
                await f(*message[1:])
        except Exception as e:
            print(e)
        if self.firstRun:
            await self.send_render()
            self.firstRun = False


class ihf():
    def __init__(self, app, template):
        self.app = app
        with open(template) as f:
            self.template = f.read()
            f.close()

    async def parse(self, websocket, path):
        client = Client(websocket, self.template, self.app)
        while (True):
            try:
                await client.recv()
            except Exception as e:
                print(e)
                break

    def serve(self, address="localhost", port=8765):
        start_server = websockets.serve(self.parse, address, port)
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()
