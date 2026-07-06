from enum import Enum


class OrderSuccessMessage(str, Enum):
    ORDER_PLACED = "Order placed successfully."


class OrderErrorMessage(str, Enum):
    ORDER_NOT_FOUND = "Order not found."
    INSUFFICIENT_BALANCE = "Insufficient balance to place this order."
    RESTAURANT_CLOSED = "Restaurant is currently closed."
    ITEM_UNAVAILABLE = "One or more items are unavailable or out of stock."
    PRICE_CHANGED = "Item prices have changed. Please recheck your order and try again."
    OWN_RESTAURANT_ORDER = "You cannot place order at your own restaurant."


class OrderStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    PREPARING = "preparing"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    REJECTED = "rejected"
