import asyncio
import websockets
import json
import functools


def rgetattr(obj, attr, *args):
    def _getattr(obj, attr):
        a = getattr(obj, attr, *args)
        if isinstance(a, list):
            return [dict(vars(i)) if hasattr(i, '__dict__') else i for i in a]
        else:
            return a

    return functools.reduce(_getattr, [obj] + attr.split('.'))


class Client():
    def __init__(self, websocket, template, app, attributes):
        self.websocket = websocket
        self.template = template
        self.app = app(self)
        self.firstRun = True
        self.attributes = attributes

    async def send_render(self):
        data = {a: rgetattr(self.app, a) for a in self.attributes}
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
    def __init__(self, app, template, jinja=False):
        self.app = app
        with open(template) as f:
            self.template = f.read()
            f.close()
        self.attributes = self.template.split("app['")
        self.attributes.pop(0)
        self.attributes = [a.split("']")[0] for a in self.attributes]
        self.attributes = list(dict.fromkeys(self.attributes))

    async def parse(self, websocket, path):
        client = Client(websocket, self.template, self.app, self.attributes)
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
