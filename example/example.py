from ihf import Ihf
from datetime import datetime


class Task:
    def __init__(self, name):
        self.name = name
        self.time = datetime.now().strftime("%H:%M:%S")


class Todo:
    def __init__(self, client):
        self.tasks = client.session.get_data('tasks', [])
        self.error = ''
        self.client = client

    async def add_task(self, name):
        if len(name) > 0:
            self.tasks += [Task(name)]
            self.error = ''
        else:
            self.error = 'Please enter a task'
        await self.client.send_render()

    def delete_task(self, index):
        self.tasks.pop(index)


test = Ihf(Todo, 'example_template.html', host='localhost', port=1910)
test.serve()
