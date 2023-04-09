from sqlalchemy.orm import Session

from app.models import (
    Mailbox,
    MailboxCreateSchema,
    Message,
    MessageCreateSchema,
    Order,
    Sender,
    SenderCreateSchema,
    User,
)


def create_user(users_db: Session, user_id: int) -> User:
    user = User(user_id=user_id)
    users_db.add(user)
    users_db.commit()
    users_db.refresh(user)
    return user


def get_user_by_id(users_db: Session, user_id: int) -> User:
    return users_db.query(User).filter(User.user_id == user_id).first()


def get_or_create_user(users_db: Session, user_id: int) -> User:
    user = get_user_by_id(users_db, user_id)
    if not user:
        user = create_user(users_db, user_id)
    return user


def create_mailbox(users_db: Session, user: User, mailbox_schema: MailboxCreateSchema) -> Mailbox:
    mailbox = Mailbox(user_id=user.user_id, **mailbox_schema.dict())
    users_db.add(mailbox)
    users_db.commit()
    users_db.refresh(mailbox)
    return mailbox


def get_user_mailboxes(user: User) -> list[Mailbox]:
    return user.mailboxes


def get_mailbox_by_id(users_db: Session, mailbox_id: int) -> Mailbox:
    return users_db.query(Mailbox).filter(Mailbox.mailbox_id == mailbox_id).first()


def get_mailbox_by_email(users_db: Session, email: str) -> Mailbox:
    return users_db.query(Mailbox).filter(Mailbox.email == email).first()


def set_user_active_mailbox(users_db: Session, user: User, mailbox_id: int) -> User:
    user.active_mailbox_id = mailbox_id
    users_db.commit()
    users_db.refresh(user)
    return user


def get_user_active_mailbox(users_db: Session, user: User) -> Mailbox:
    return get_mailbox_by_id(users_db, user.active_mailbox_id)


def create_sender(mail_db: Session, sender_schema: SenderCreateSchema) -> Sender:
    sender = Sender(**sender_schema.dict())
    mail_db.add(sender)
    mail_db.commit()
    mail_db.refresh(sender)
    return sender


def get_sender_by_email(mail_db: Session, email: str) -> Sender:
    return mail_db.query(Sender).filter(Sender.email == email).first()


def get_or_create_sender(mail_db: Session, sender_schema: SenderCreateSchema) -> Sender:
    sender = get_sender_by_email(mail_db, sender_schema.email)
    if not sender:
        sender = create_sender(mail_db, sender_schema)
    return sender


def create_message(mail_db: Session, message: MessageCreateSchema) -> Message:
    message = Message(**message.dict())
    mail_db.add(message)
    mail_db.commit()
    mail_db.refresh(message)
    return message


def get_message_by_uid(mail_db: Session, uid: int) -> Message:
    return mail_db.query(Message).filter(Message.uid == uid).first()


def message_exists(mail_db: Session, uid: int) -> bool:
    return mail_db.query(Message).filter(Message.uid == uid).first() is not None


def get_messages_by_sender(mail_db: Session, sender: Sender) -> list[Message]:
    return mail_db.query(Message).filter(Message.sender_id == sender.id).all()


def get_messages_by_order(order: Order) -> list[Message]:
    return order.messages


def get_or_create_order(mail_db: Session, order_number: str) -> Order:
    order = mail_db.query(Order).filter(Order.order_number == order_number).first()
    if order:
        return order
    order = Order(order_number=order_number)
    mail_db.add(order)
    mail_db.commit()
    mail_db.refresh(order)
    return order


def assign_order_to_message(mail_db: Session, message: Message, order: Order) -> None:
    message.order_number = order.order_number
    mail_db.commit()
    mail_db.refresh(message)
