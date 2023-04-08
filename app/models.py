from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Text
from sqlalchemy.orm import backref, declarative_base, relationship
from pydantic_sqlalchemy import sqlalchemy_to_pydantic
from pydantic import Extra



UsersBase = declarative_base()
MailboxBase = declarative_base()


class User(UsersBase):
    __tablename__ = "user"
    user_id = Column(Integer, primary_key=True)
    active_mailbox_id = Column(Integer, nullable=True)
    mailboxes = relationship("Mailbox", backref=backref("user"))

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


# Now Mailbox is creates with only one mail folder that can not be changed.
# It can be resolved by creating a new table with mail folders
# and particular database for each folder
# or (worse)
# by allowing to create many mailboxes with the same email and different folders.
class Mailbox(UsersBase):
    __tablename__ = "mailbox"
    mailbox_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.user_id"))
    email = Column(String, unique=True)
    password = Column(String)
    imap_server_url = Column(String, default="imap.yandex.ru")
    imap_port = Column(Integer, default=993)
    mail_folder = Column(String, default="INBOX")

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class Sender(MailboxBase):
    __tablename__ = "sender"
    sender_id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True)
    name = Column(String, nullable=True)
    messages = relationship("Message", backref=backref("sender"))


class Message(MailboxBase):
    __tablename__ = "message"
    uid = Column(Integer, primary_key=True)
    sender_id = Column(Integer, ForeignKey("sender.sender_id"))
    subject = Column(String, nullable=True)
    content = Column(Text)
    date = Column(DateTime)
    order_number = Column(String, ForeignKey("order.order_number"), nullable=True)


class Order(MailboxBase):
    __tablename__ = "order"
    order_number = Column(String, primary_key=True)
    messages = relationship("Message", backref=backref("order"))


MailboxCreateSchema = sqlalchemy_to_pydantic(Mailbox, exclude=["mailbox_id", "user_id"])
MessageCreateSchema = sqlalchemy_to_pydantic(Message)
SenderCreateSchema = sqlalchemy_to_pydantic(Sender, exclude=["sender_id", "messages"])

# Class to store user's mailbox data after closing the connection to users_db
class MailboxSchema(sqlalchemy_to_pydantic(Mailbox)):
    
    class Config:
        extra = Extra.ignore


# MailboxSetupSchema = sqlalchemy_to_pydantic(Mailbox, exclude=["user_id"], config={"extra": Extra.ignore})
