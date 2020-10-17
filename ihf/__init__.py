import asyncio
import websockets
import json
import re
import inspect
from bs4 import BeautifulSoup as bs
import html


def open_template(template):
    with open(template) as f:
        result = f.read()
        f.close()
    result = re.sub('(?<={%)(.*)(?=%})', lambda x: open_template(x.group()), result)
    result = result.replace('{%', '').replace('%}', '')
    return result


def convert_for(full, attr):
    attr_split = attr.split('in')
    var = attr_split[0].strip()
    list = attr_split[1].strip()
    full = full.replace('for="'+html.escape(attr)+'"', '')
    result = '${' + list + '.map((' + var + ') => `' + full + '`).join(\'\')}'
    return result


def convert_if(full, attr):
    full = full.replace('if="'+html.escape(attr)+'"', '')
    result = '${' + attr + ' ? `' + full + '` : \'\'}'
    return result


def split_html_tag(full):
    start = full[:full.index('>') + 1]
    full_reverse = full[::-1]
    end = full_reverse[:full_reverse.index('<') + 1][::-1]
    content = full.replace(start, '').replace(end, '')
    return start, content, end


def convert_template(template):
    result = template
    soup = bs(result, features="lxml")
    result = str(soup)
    for t in soup.html.find_all(recursive=True):
        if 'if' in t.attrs.keys():
            full = str(t)
            result = result.replace(full, convert_if(full, t.attrs['if']))
        if 'for' in t.attrs.keys():
            full = str(t)
            #start, content, end = split_html_tag(full)
            result = result.replace(full, convert_for(full, t.attrs['for']))
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
        return {i: rgetattr(value[i]) for i in value.keys() if not i.startswith('_')}
    if hasattr(value, '__dict__'):
        return {i: rgetattr(value, i) for i in vars(value).keys() if not i.startswith('_')}
    return value


class Client():
    def __init__(self, websocket, template, app):
        self.websocket = websocket
        self.template = template
        self.app = app
        self.firstRun = True
        self.previous_send = {}
        self.cookie = {}

    async def send_render(self, force=False):
        to_send = {'data': rgetattr(self.app), 'cookie': self.cookie}
        if self.firstRun:
            to_send['template'] = self.template
        to_send = json.dumps(to_send)
        if force or (to_send != self.previous_send):
            self.previous_send = to_send
            await self.websocket.send(str(to_send))

    async def recv(self):
        message = await self.websocket.recv()
        try:
            if self.firstRun:
                if len(message) > 0:
                    self.cookie = {c.split('=')[0]: c.split('=')[1] for c in message.split(';') if '=' in c}
                self.app = self.app(self)
            else:
                message = eval(message)
                objs = message[0].split('.')
                o = self.app
                while len(objs) > 0:
                    if not objs[0].startswith('_') and objs[0] in dir(o):
                        f = getattr(o, objs[0])
                        o = getattr(o, objs.pop(0))
                if message[0] in self.template:
                    if inspect.iscoroutinefunction(f):
                        await f(*message[1:])
                    else:
                        f(*message[1:])
                        await self.send_render()
        except Exception as e:
            print(e)
        if self.firstRun:
            await self.send_render()
            self.firstRun = False


class ihf():
    def __init__(self, app, template_name):
        self.app = app
        self.template = convert_template(open_template(template_name))

    async def parse(self, websocket, path):
        client = Client(websocket, self.template, self.app)
        while True:
            try:
                await client.recv()
            except Exception as e:
                print(e)
                break

    def serve(self, host="localhost", port=8765, ssl_context=None):
        start_server = websockets.serve(self.parse, host, port, ssl=ssl_context)
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()
