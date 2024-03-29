import inspect
import json
import base64
import traceback


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
    def __init__(self, websocket, template, app, sessions_manager, file_manager):
        self.websocket = websocket
        self.template = template
        self.app = app
        self.firstRun = True
        self.previous_send = {}
        self.cookie = {}
        self.sessions_manager = sessions_manager
        self.file_manager = file_manager
        self.session = None

    async def send_render(self, force=False):
        to_send = {'data': rgetattr(self.app), 'cookie': self.cookie}
        if self.firstRun:
            to_send['template'] = self.template
        to_send = json.dumps(to_send)
        #if force or (to_send != self.previous_send):
        #    self.previous_send = to_send
        #    await self.websocket.send(str(to_send))
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
                if message.startswith('file:'):
                    message = eval(message.replace('file:', ''))
                    file = self.file_manager.get_new_file(message[1], folder=self.session.id, is_temp=True, is_private=True)
                    o = file.open(mode='wb')
                    o.write(base64.urlsafe_b64decode(message[2].split('base64,')[1]))
                    o.close()
                    message = [message[0], file]
                else:
                    message = eval(message)
                objs = message[0].split('.')
                o = self.app
                while len(objs) > 0:
                    temp = objs
                    if not objs[0].startswith('_') and objs[0] in dir(o):
                        f = getattr(o, objs[0])
                        o = getattr(o, objs.pop(0))
                    if objs == temp and len(objs) > 0:
                        raise Exception('Problem with message', message)
                if message[0] in self.template:
                    if inspect.iscoroutinefunction(f):
                        await f(*message[1:])
                    else:
                        f(*message[1:])
                        await self.send_render()
        except Exception as e:
            print(traceback.format_exc())
            await self.websocket.close()
        if self.firstRun:
            await self.send_render()
            self.firstRun = False
