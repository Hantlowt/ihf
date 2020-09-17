from ihf import ihf
from datetime import datetime


class Task:
    def __init__(self, name):
        self.name = name
        self.time = datetime.now().strftime("%H:%M:%S")


class Todo:
    def __init__(self, client):
        self.tasks = [Task('coucou')]
        self.client = client
        self.error = ''

    async def add_task(self, name):
        if len(name) > 0:
            self.tasks += [Task(name)]
            self.error = ''
        else:
            self.error = 'Please enter a task'
        await self.client.send_render()

    async def delete_task(self, index):
        self.tasks.pop(index)
        await self.client.send_render()


test = ihf(Todo, 'example.html')
test.serve()
