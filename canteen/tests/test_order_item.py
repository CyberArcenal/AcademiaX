from django.test import TestCase
from decimal import Decimal
from users.models import User
from canteen.models import Category, Product, Order, OrderItem
from canteen.services.order_item import OrderItemService
from canteen.serializers.order_item import (
    OrderItemCreateSerializer,
    OrderItemUpdateSerializer,
    OrderItemDisplaySerializer,
)
from common.enums.canteen import ProductCategory, OrderType, OrderStatus


class OrderItemModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="customer", email="cust@example.com", password="test")
        self.category = Category.objects.create(name=ProductCategory.RICE_MEAL)
        self.product = Product.objects.create(
            name="Chicken Rice",
            category=self.category,
            price=Decimal('120.00')
        )
        self.order = Order.objects.create(
            user=self.user,
            order_number="ORD-001",
            order_type=OrderType.DINE_IN,
            status=OrderStatus.PENDING
        )

    def test_create_order_item(self):
        item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            unit_price=Decimal('120.00')
        )
        self.assertEqual(item.order, self.order)
        self.assertEqual(item.product, self.product)
        self.assertEqual(item.quantity, 2)

    def test_subtotal_auto_calculation(self):
        item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=3,
            unit_price=Decimal('100.00')
        )
        self.assertEqual(item.subtotal, Decimal('300.00'))

    def test_str_method(self):
        item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=1,
            unit_price=Decimal('50.00')
        )
        expected = f"{self.order.order_number} - {self.product.name} x1"
        self.assertEqual(str(item), expected)


class OrderItemServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="customer2", email="cust2@example.com", password="test")
        self.category = Category.objects.create(name=ProductCategory.DRINKS)
        self.product = Product.objects.create(
            name="Soda",
            category=self.category,
            price=Decimal('30.00'),
            stock_quantity=10
        )
        self.order = Order.objects.create(
            user=self.user,
            order_number="ORD-002",
            order_type=OrderType.TAKE_OUT
        )

    def test_add_item_to_order(self):
        item = OrderItemService.add_item_to_order(
            order=self.order,
            product=self.product,
            quantity=2
        )
        self.assertEqual(item.order, self.order)
        self.assertEqual(item.product, self.product)
        self.assertEqual(item.quantity, 2)

    def test_add_existing_item_increases_quantity(self):
        OrderItem.objects.create(order=self.order, product=self.product, quantity=1, unit_price=self.product.price)
        item = OrderItemService.add_item_to_order(self.order, self.product, quantity=2)
        self.assertEqual(item.quantity, 3)

    def test_get_items_by_order(self):
        OrderItem.objects.create(order=self.order, product=self.product, quantity=1, unit_price=self.product.price)
        items = OrderItemService.get_items_by_order(self.order.id)
        self.assertEqual(items.count(), 1)

    def test_update_quantity(self):
        item = OrderItem.objects.create(order=self.order, product=self.product, quantity=1, unit_price=self.product.price)
        updated = OrderItemService.update_quantity(item, 5)
        self.assertEqual(updated.quantity, 5)

    def test_remove_item(self):
        item = OrderItem.objects.create(order=self.order, product=self.product, quantity=1, unit_price=self.product.price)
        success = OrderItemService.remove_item(item)
        self.assertTrue(success)
        with self.assertRaises(OrderItem.DoesNotExist):
            OrderItem.objects.get(id=item.id)


class OrderItemSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="customer3", email="cust3@example.com", password="test")
        self.category = Category.objects.create(name=ProductCategory.SNACKS)
        self.product = Product.objects.create(
            name="Chips",
            category=self.category,
            price=Decimal('45.00')
        )
        self.order = Order.objects.create(
            user=self.user,
            order_number="ORD-003"
        )

    def test_create_serializer_valid(self):
        data = {
            "order_id": self.order.id,
            "product_id": self.product.id,
            "quantity": 2
        }
        serializer = OrderItemCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        item = serializer.save()
        self.assertEqual(item.order, self.order)

    def test_update_serializer(self):
        item = OrderItem.objects.create(order=self.order, product=self.product, quantity=1, unit_price=self.product.price)
        data = {"quantity": 4}
        serializer = OrderItemUpdateSerializer(item, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.quantity, 4)

    def test_display_serializer(self):
        item = OrderItem.objects.create(order=self.order, product=self.product, quantity=1, unit_price=self.product.price)
        serializer = OrderItemDisplaySerializer(item)
        self.assertEqual(serializer.data["order"]["id"], self.order.id)
        self.assertEqual(serializer.data["product"]["id"], self.product.id)