from django.test import TestCase
from decimal import Decimal
from users.models import User
from students.models import Student
from canteen.models import Order, Category, Product
from canteen.services.order import OrderService
from canteen.serializers.order import (
    OrderCreateSerializer,
    OrderUpdateSerializer,
    OrderDisplaySerializer,
)
from common.enums.canteen import OrderType, OrderStatus


class OrderModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="customer", email="cust@example.com", password="test")

    def test_create_order_with_user(self):
        order = Order.objects.create(
            user=self.user,
            order_number="ORD-20250101-0001",
            order_type=OrderType.DINE_IN,
            status=OrderStatus.PENDING,
            total_amount=Decimal('0')
        )
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.order_type, OrderType.DINE_IN)

    def test_str_method(self):
        order = Order.objects.create(user=self.user, order_number="ORD-001")
        self.assertEqual(str(order), f"Order ORD-001 - {self.user}")


class OrderServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="customer2", email="cust2@example.com", password="test")
        self.student = Student.objects.create(
            first_name="Juan",
            last_name="Dela Cruz",
            birth_date="2010-01-01",
            gender="M"
        )

    def test_generate_order_number(self):
        order_num = OrderService.generate_order_number()
        self.assertTrue(order_num.startswith("ORD-"))

    def test_create_order_with_student(self):
        order = OrderService.create_order(
            order_type=OrderType.TAKE_OUT,
            student=self.student
        )
        self.assertEqual(order.student, self.student)
        self.assertEqual(order.status, OrderStatus.PENDING)

    def test_get_pending_orders(self):
        Order.objects.create(user=self.user, order_number="ORD-001", status=OrderStatus.PENDING)
        Order.objects.create(user=self.user, order_number="ORD-002", status=OrderStatus.COMPLETED)
        pending = OrderService.get_pending_orders()
        self.assertEqual(pending.count(), 1)

    def test_update_order_status(self):
        order = Order.objects.create(user=self.user, order_number="ORD-001", status=OrderStatus.PENDING)
        updated = OrderService.update_order_status(order, OrderStatus.PREPARING)
        self.assertEqual(updated.status, OrderStatus.PREPARING)

    def test_cancel_order(self):
        order = Order.objects.create(user=self.user, order_number="ORD-001", status=OrderStatus.PENDING)
        updated = OrderService.cancel_order(order, "Customer requested")
        self.assertEqual(updated.status, OrderStatus.CANCELLED)
        self.assertEqual(updated.cancelled_reason, "Customer requested")


class OrderSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="customer3", email="cust3@example.com", password="test")
        self.student = Student.objects.create(
            first_name="Maria",
            last_name="Santos",
            birth_date="2010-02-02",
            gender="F"
        )

    def test_create_serializer_valid_with_student(self):
        data = {
            "order_type": OrderType.DINE_IN,
            "student_id": self.student.id,
            "notes": "Extra rice"
        }
        serializer = OrderCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        order = serializer.save()
        self.assertEqual(order.student, self.student)

    def test_update_serializer(self):
        order = Order.objects.create(user=self.user, order_number="ORD-001", status=OrderStatus.PENDING)
        data = {"status": OrderStatus.COMPLETED}
        serializer = OrderUpdateSerializer(order, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.status, OrderStatus.COMPLETED)

    def test_display_serializer(self):
        order = Order.objects.create(user=self.user, order_number="ORD-001", total_amount=Decimal('150.00'))
        serializer = OrderDisplaySerializer(order)
        self.assertEqual(serializer.data["order_number"], "ORD-001")
        self.assertEqual(serializer.data["user"]["id"], self.user.id)