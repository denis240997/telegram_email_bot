import os
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session

from app.models import MailboxBase, MailboxSchema, UsersBase

ECHO_DB_ACTIONS = os.getenv("ECHO_DB_ACTIONS", False)

SQLITE_USERS_DB_PATH = os.path.join("db", "email.sqlite")
SQLITE_MAIL_DB_PATH = os.path.join("db", "users")


@contextmanager
def get_users_db() -> Session:
    engine = create_engine(f"sqlite:///{SQLITE_USERS_DB_PATH}", echo=ECHO_DB_ACTIONS)
    UsersBase.metadata.create_all(engine)
    Session = sessionmaker()
    Session.configure(bind=engine)
    session = Session()
    try:
        yield session
        session.commit()
    except BaseException as error:
        session.rollback()
        raise error
    finally:
        session.close()


class MailboxNotExistsError(Exception):
    pass


@contextmanager
def get_mail_db(mailbox: MailboxSchema) -> Session:
    if mailbox is None:
        raise MailboxNotExistsError("Mailbox is None")
    
    mailbox_id = mailbox.mailbox_id
    user_id = mailbox.user_id
    sqlite_mail_db_path = os.path.join(SQLITE_MAIL_DB_PATH, f"{user_id}_{mailbox_id}.sqlite")
    engine = create_engine(f"sqlite:///{sqlite_mail_db_path}", echo=ECHO_DB_ACTIONS)
    MailboxBase.metadata.create_all(engine)
    Session = sessionmaker()
    Session.configure(bind=engine)
    session = Session()
    try:
        yield session
        session.commit()
    except BaseException as error:
        session.rollback()
        raise error
    finally:
        session.close()
