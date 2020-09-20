import asyncio
import websockets
import json
import re


def open_template(template):
    with open(template) as f:
        result = f.read()
        f.close()
    result = re.sub('(?<={%)(.*)(?=%})', lambda x: open_template(x.group()), result)
    result = result.replace('{%', '').replace('%}', '')
    return result


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


def rgetattr(obj, attr=None):
    value = obj
    if type(attr) == str and hasattr(obj, '__dict__'):
        value = getattr(obj, attr)
    if type(value) == Client:
        return None
    if isinstance(value, list):
        return [rgetattr(i) for i in value]
    if isinstance(value, dict):
        return {i: rgetattr(i) for i in value.keys() if not i.startswith('_')}
    if hasattr(value, '__dict__'):
        return {i: rgetattr(value, i) for i in vars(value).keys() if not i.startswith('_')}
    return value


class Client():
    def __init__(self, websocket, template, app):
        self.websocket = websocket
        self.template = template
        self.app = app(self)
        self.firstRun = True
        self.previous_data = {}

    async def send_render(self, force=False):
        data = rgetattr(self.app)
        if self.firstRun:
            data['template'] = self.template
        data = json.dumps(data)
        if force or (data != self.previous_data):
            self.previous_data = data
            await self.websocket.send(str(data))

    async def recv(self):
        message = await self.websocket.recv()
        try:
            message = eval(message)
            print(message)
            if not message[0].startswith('_') and message[0] in dir(self.app):
                f = getattr(self.app, message[0])
                await f(*message[1:])
        except Exception as e:
            print(e)
        if self.firstRun:
            await self.send_render()
            self.firstRun = False


class ihf():
    def __init__(self, app, template_name):
        self.app = app
        self.template = open_template(template_name)

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
