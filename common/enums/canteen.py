# common/enums/canteen.py
from django.db import models

class ProductCategory(models.TextChoices):
    RICE_MEAL = 'RM', 'Rice Meal'
    NOODLES = 'ND', 'Noodles'
    SANDWICH = 'SW', 'Sandwich'
    DRINKS = 'DR', 'Drinks'
    SNACKS = 'SK', 'Snacks'
    DESSERT = 'DS', 'Dessert'
    FRUIT = 'FR', 'Fruit'
    OTHER = 'OT', 'Other'

class OrderStatus(models.TextChoices):
    PENDING = 'PD', 'Pending'
    PREPARING = 'PR', 'Preparing'
    READY = 'RD', 'Ready for Pickup'
    COMPLETED = 'CP', 'Completed'
    CANCELLED = 'CN', 'Cancelled'

class PaymentMethod(models.TextChoices):
    CASH = 'CS', 'Cash'
    CARD = 'CD', 'Debit/Credit Card'
    QR = 'QR', 'QR Code'
    SCHOOL_ID = 'ID', 'School ID (Load Wallet)'

class OrderType(models.TextChoices):
    DINE_IN = 'DI', 'Dine In'
    TAKE_OUT = 'TO', 'Take Out'
    DELIVERY = 'DL', 'Delivery'