import os
from datetime import date

from app.db import get_users_db, get_mail_db
from app.crud import get_user_by_id, get_mailbox_by_email, create_message, get_messages_by_sender, get_or_create_user, get_user_mailboxes, create_mailbox
from app.models import MailboxCreateSchema, SenderCreateSchema, MailboxSchema
from app.mailing_tools import get_mailbox, process_unseen_messages, process_messages_since_date


CHAT_ID = os.getenv('CHAT_ID')
USER_EMAIL = os.getenv('USER_EMAIL')
USER_PASSWORD = os.getenv('USER_PASSWORD')


with get_users_db() as users_db:
    user = get_or_create_user(users_db, CHAT_ID)

    mailbox_schema = MailboxCreateSchema(
        email=USER_EMAIL,
        password=USER_PASSWORD,
    )
    mailbox_schema_1 = MailboxCreateSchema(
        email=USER_EMAIL + '_1',
        password=USER_PASSWORD + '_1',
    )
    create_mailbox(users_db, user, mailbox_schema)
    create_mailbox(users_db, user, mailbox_schema_1)

    mailbox_list = get_user_mailboxes(user)
    # User can chose mailbox from list or create new one
    for mailbox in mailbox_list:
        print(mailbox.email)

    mailbox = get_mailbox_by_email(users_db, USER_EMAIL).to_dict()
    mailbox_db = MailboxSchema(**mailbox)
    # mailbox_setup = MailboxSetupSchema(**mailbox)
    

# with get_mail_db(mailbox_db) as mail_db, get_mailbox(**{key: val for key, val in mailbox.items() if key not in ("user_id", "mailbox_id")}) as mb:
#     # process_unseen_messages(mail_db, mb)
#     # print(datetime(2018, 1, 1))
#     process_messages_since_date(mail_db, mb, date(2018, 1, 1))
