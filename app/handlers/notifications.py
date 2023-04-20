import re
import asyncio

from pyrogram import Client
from pyrogram.types import Message
from sqlalchemy import event
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import Event

from app.crud import get_order_items
from app.models import Item, Order, OrderStatus


def stringify_item(item: Item, amount: int) -> str:
    size_repr = f"Size: {item.size} " if item.size else ""
    amount_repr = f" x{amount}\t" if amount > 1 else "\t"
    return f"{amount_repr}{item.name}\t({item.sku})\t{size_repr}\t- {item.price} RUB.\n"


def stringify_order(order: Order) -> str:
    order_repr = order.creation_date.strftime("%d.%m.%Y %H:%M") + "\n"
    order_repr += f"Order {order.order_number}:\n"
    order_repr += f"CDEK number: {order.cdek_number}\n"
    order_repr += f"Customer phone: {order.customer_phone}\n"
    order_repr += f"Delivery city: {order.delivery_city}\n\n"
    for item, amount in get_order_items(order):
        order_repr += stringify_item(item, amount)
    return order_repr


def register_notifications(client: Client) -> None:
    loop = asyncio.get_event_loop()

    def notify_on_order_accepted_to_delivery(
        target: Order, value: str, old_value: str, initiator: Event
    ) -> None:
        if value == OrderStatus.ACCEPTED_TO_DELIVERY and value != old_value:
            db_url = str(Session.object_session(target).get_bind().url)
            db_url_user_id_regex = re.compile(r".+/(\d+)_")
            user_id = db_url_user_id_regex.match(db_url).groups()[0]
            loop.create_task(client.send_message(user_id, stringify_order(target)))

    event.listen(Order.status, "set", notify_on_order_accepted_to_delivery)
