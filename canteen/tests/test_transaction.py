from django.test import TestCase
from decimal import Decimal
from users.models import User
from canteen.models import Category, Product, Order, PaymentTransaction
from canteen.services.transaction import PaymentTransactionService
from canteen.serializers.transaction import (
    PaymentTransactionCreateSerializer,
    PaymentTransactionUpdateSerializer,
    PaymentTransactionDisplaySerializer,
)
from common.enums.canteen import ProductCategory, OrderType, OrderStatus, PaymentMethod


class PaymentTransactionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="cashier", email="cashier@example.com", password="test")
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
            total_amount=Decimal('120.00')
        )

    def test_create_transaction(self):
        transaction = PaymentTransaction.objects.create(
            order=self.order,
            amount_paid=Decimal('200.00'),
            change_due=Decimal('80.00'),
            payment_method=PaymentMethod.CASH,
            received_by=self.user
        )
        self.assertEqual(transaction.order, self.order)
        self.assertEqual(transaction.amount_paid, Decimal('200.00'))
        self.assertEqual(transaction.payment_method, PaymentMethod.CASH)

    def test_str_method(self):
        transaction = PaymentTransaction.objects.create(
            order=self.order,
            amount_paid=Decimal('120.00'),
            change_due=Decimal('0.00')
        )
        expected = f"Payment for {self.order.order_number} - ₱120.00"
        self.assertEqual(str(transaction), expected)


class PaymentTransactionServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="cashier2", email="cashier2@example.com", password="test")
        self.category = Category.objects.create(name=ProductCategory.DRINKS)
        self.product = Product.objects.create(
            name="Soda",
            category=self.category,
            price=Decimal('30.00')
        )
        self.order = Order.objects.create(
            user=self.user,
            order_number="ORD-002",
            total_amount=Decimal('60.00'),
            status=OrderStatus.PENDING
        )

    def test_process_payment(self):
        transaction = PaymentTransactionService.process_payment(
            order=self.order,
            amount_paid=Decimal('100.00'),
            payment_method=PaymentMethod.CASH,
            received_by=self.user
        )
        self.assertEqual(transaction.amount_paid, Decimal('100.00'))
        self.assertEqual(transaction.change_due, Decimal('40.00'))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, OrderStatus.COMPLETED)

    def test_insufficient_payment_fails(self):
        with self.assertRaises(Exception):
            PaymentTransactionService.process_payment(
                order=self.order,
                amount_paid=Decimal('50.00'),
                payment_method=PaymentMethod.CASH
            )

    def test_get_transaction_by_order(self):
        PaymentTransaction.objects.create(order=self.order, amount_paid=60, change_due=0, payment_method=PaymentMethod.CASH)
        transaction = PaymentTransactionService.get_transaction_by_order(self.order.id)
        self.assertIsNotNone(transaction)

    def test_get_daily_sales(self):
        from datetime import date
        PaymentTransaction.objects.create(
            order=self.order, amount_paid=60, change_due=0, payment_method=PaymentMethod.CASH, paid_at=date.today()
        )
        sales = PaymentTransactionService.get_daily_sales(date.today())
        self.assertEqual(sales['total_sales'], Decimal('60.00'))
        self.assertEqual(sales['transaction_count'], 1)


class PaymentTransactionSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="cashier3", email="cashier3@example.com", password="test")
        self.category = Category.objects.create(name=ProductCategory.SNACKS)
        self.product = Product.objects.create(
            name="Chips",
            category=self.category,
            price=Decimal('45.00')
        )
        self.order = Order.objects.create(
            user=self.user,
            order_number="ORD-003",
            total_amount=Decimal('45.00')
        )

    def test_create_serializer_valid(self):
        data = {
            "order_id": self.order.id,
            "amount_paid": "50.00",
            "payment_method": PaymentMethod.CASH,
            "received_by_id": self.user.id
        }
        serializer = PaymentTransactionCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        transaction = serializer.save()
        self.assertEqual(transaction.order, self.order)

    def test_update_serializer(self):
        transaction = PaymentTransaction.objects.create(
            order=self.order, amount_paid=50, change_due=5, payment_method=PaymentMethod.CASH
        )
        data = {"reference_number": "REF123", "notes": "Updated"}
        serializer = PaymentTransactionUpdateSerializer(transaction, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.reference_number, "REF123")

    def test_display_serializer(self):
        transaction = PaymentTransaction.objects.create(
            order=self.order, amount_paid=50, change_due=5, payment_method=PaymentMethod.CASH
        )
        serializer = PaymentTransactionDisplaySerializer(transaction)
        self.assertEqual(serializer.data["order"]["id"], self.order.id)
        self.assertEqual(serializer.data["amount_paid"], "50.00")