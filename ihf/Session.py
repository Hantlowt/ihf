import uuid


class Session:
    def __init__(self, session_id):
        self.id = session_id
        self.data = {}

    def get_data(self, key, default=None):
        if key not in self.data.keys():
            self.data[key] = default
        return self.data[key]


class SessionManager:
    def __init__(self):
        self.sessions = {}

    def get_session(self, sessions_id=None):
        sessions_id = sessions_id if sessions_id else uuid.uuid4().hex
        if sessions_id not in self.sessions.keys():
            self.sessions[sessions_id] = Session(sessions_id)
        return self.sessions[sessions_id]
