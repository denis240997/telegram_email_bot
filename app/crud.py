from sqlalchemy.orm import Session

from app.models import (
    Item,
    ItemCreateSchema,
    Mailbox,
    MailboxCreateSchema,
    Message,
    MessageCreateSchema,
    MessageStatus,
    Order,
    OrderCreateSchema,
    Sender,
    SenderCreateSchema,
    User,
    OrderItem,
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


def delete_mailbox_by_id(users_db: Session, mailbox_id: int) -> None:
    mailbox = users_db.query(Mailbox).filter(Mailbox.mailbox_id == mailbox_id).one()
    users_db.delete(mailbox)
    users_db.commit()


def get_user_mailboxes(user: User) -> list[Mailbox]:
    return user.mailboxes


def get_mailbox_by_id(users_db: Session, mailbox_id: int) -> Mailbox:
    return users_db.query(Mailbox).filter(Mailbox.mailbox_id == mailbox_id).first()


def get_mailbox_by_email(users_db: Session, email: str) -> Mailbox:
    return users_db.query(Mailbox).filter(Mailbox.email == email).first()


def update_mailbox(users_db: Session, mailbox_schema: MailboxCreateSchema) -> Mailbox:
    mailbox = get_mailbox_by_id(users_db, mailbox_schema.mailbox_id)
    for key, value in mailbox_schema.dict().items():
        if getattr(mailbox, key) != value:
            setattr(mailbox, key, value)

    users_db.commit()
    users_db.refresh(mailbox)
    return mailbox


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


def create_message(mail_db: Session, message_schema: MessageCreateSchema) -> Message:
    message = Message(**message_schema.dict())
    mail_db.add(message)
    mail_db.commit()
    mail_db.refresh(message)
    return message


def get_message_by_uid(mail_db: Session, uid: int) -> Message:
    return mail_db.query(Message).filter(Message.uid == uid).first()


def get_or_create_message(mail_db: Session, message_schema: MessageCreateSchema) -> Message:
    message = get_message_by_uid(mail_db, message_schema.uid)
    if not message:
        message = create_message(mail_db, message_schema)
    return message


def message_exists(mail_db: Session, uid: int) -> bool:
    return mail_db.query(Message).filter(Message.uid == uid).first() is not None


def get_messages_by_sender(mail_db: Session, sender: Sender) -> list[Message]:
    return mail_db.query(Message).filter(Message.sender_id == sender.id).all()


def get_messages_by_sender_with_status(mail_db: Session, sender: Sender, status: MessageStatus) -> list[Message]:
    return mail_db.query(Message).filter(Message.sender_id == sender.sender_id, Message.status == status).all()


def mark_message_processed(mail_db: Session, message: Message) -> Message:
    message.status = MessageStatus.PROCESSED
    message.content = None
    mail_db.commit()
    mail_db.refresh(message)
    return message


def assign_order_to_message(mail_db: Session, message: Message, order: Order) -> Message:
    message.order_number = order.order_number
    mail_db.commit()
    mail_db.refresh(message)
    return message


def create_order(mail_db: Session, order_schema: OrderCreateSchema) -> Order:
    order = Order(**order_schema.dict())
    mail_db.add(order)
    mail_db.commit()
    mail_db.refresh(order)
    return order


def get_order_by_number(mail_db: Session, order_number: str) -> Order:
    return mail_db.query(Order).filter(Order.order_number == order_number).first()


def get_or_create_order(mail_db: Session, order_schema: OrderCreateSchema) -> Order:
    order = get_order_by_number(mail_db, order_schema.order_number)
    if not order:
        order = create_order(mail_db, order_schema)
    return order


def add_cdek_number_to_order(mail_db: Session, order: Order, cdek_number: str) -> Order:
    order.cdek_number = cdek_number
    mail_db.commit()
    mail_db.refresh(order)
    return order


def get_messages_by_order(order: Order) -> list[Message]:
    return order.messages


def create_item(mail_db: Session, item_schema: ItemCreateSchema) -> Item:
    item = Item(**item_schema.dict())
    mail_db.add(item)
    mail_db.commit()
    mail_db.refresh(item)
    return item


def get_item_by_sku(mail_db: Session, sku: str) -> Item:
    return mail_db.query(Item).filter(Item.sku == sku).first()


def get_or_create_item(mail_db: Session, item_schema: ItemCreateSchema) -> Item:
    item = get_item_by_sku(mail_db, item_schema.sku)
    if not item:
        item = create_item(mail_db, item_schema)
    return item


def add_items_to_order(mail_db: Session, order: Order, items: list[tuple[Item, int]]) -> Order:
    for item, quantity in items:
        order_item = OrderItem(order=order, item=item, quantity=quantity)
        order.order_items.append(order_item)
    mail_db.add(order)
    mail_db.commit()
    mail_db.refresh(order)
    return order


def get_order_items(order: Order) -> list[tuple[Item, int]]:
    return [(order_item.item, order_item.quantity) for order_item in order.order_items]


def get_item_orders(item: Item) -> list[Order]:
    return [order_item.order for order_item in item.order_items]
