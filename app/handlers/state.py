from app.models import MailboxSchema


class UserMailbox:
    def __init__(self):
        self._data: MailboxSchema = None

    def set(self, value):
        self._data = value

    def get(self):
        return self._data

    def clear(self):
        self._data = None


user_mailbox = UserMailbox()
