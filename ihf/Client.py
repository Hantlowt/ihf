import inspect
import json


def rgetattr(obj, attr=None):
    value = obj
    if type(attr) == str and hasattr(obj, '__dict__'):
        value = getattr(obj, attr)
    if isinstance(value, list):
        return [rgetattr(i) for i in value]
    if isinstance(value, dict):
        return {i: rgetattr(value[i]) for i in value.keys() if not i.startswith('_')}
    if hasattr(value, '__dict__'):
        return {i: rgetattr(value, i) for i in vars(value).keys() if not i.startswith('_')
                and type(getattr(value, i)) != Client}
    return value


class Client:
    def __init__(self, websocket, template, app, sessions_manager):
        self.websocket = websocket
        self.template = template
        self.app = app
        self.firstRun = True
        self.previous_send = {}
        self.cookie = {}
        self.sessions_manager = sessions_manager
        self.session = None

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
                self.session = self.sessions_manager.get_session(self.cookie.get('sessionId'))
                self.cookie['sessionId'] = self.session.id
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
