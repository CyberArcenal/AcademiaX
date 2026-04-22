from django.test import TestCase
from decimal import Decimal
from users.models import User
from canteen.models import Category, Product, InventoryLog
from canteen.services.inventory import InventoryLogService
from canteen.serializers.inventory import (
    InventoryLogCreateSerializer,
    InventoryLogUpdateSerializer,
    InventoryLogDisplaySerializer,
)
from common.enums.canteen import ProductCategory


class InventoryLogModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="staff", email="staff@example.com", password="test")
        self.category = Category.objects.create(name=ProductCategory.RICE_MEAL)
        self.product = Product.objects.create(
            name="Chicken Rice",
            category=self.category,
            price=Decimal('120.00'),
            stock_quantity=10
        )

    def test_create_inventory_log(self):
        log = InventoryLog.objects.create(
            product=self.product,
            quantity_change=5,
            new_quantity=15,
            reason='PURCHASE',
            notes='Restock order',
            recorded_by=self.user
        )
        self.assertEqual(log.product, self.product)
        self.assertEqual(log.quantity_change, 5)
        self.assertEqual(log.reason, 'PURCHASE')

    def test_str_method(self):
        log = InventoryLog.objects.create(
            product=self.product,
            quantity_change=10,
            new_quantity=20,
            reason='PURCHASE'
        )
        expected = f"{self.product.name}: +10 -> 20"
        self.assertEqual(str(log), expected)


class InventoryLogServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="staff2", email="staff2@example.com", password="test")
        self.category = Category.objects.create(name=ProductCategory.DRINKS)
        self.product = Product.objects.create(
            name="Soda",
            category=self.category,
            price=Decimal('30.00'),
            stock_quantity=5
        )

    def test_create_log(self):
        log = InventoryLogService.create_log(
            product=self.product,
            quantity_change=10,
            reason='PURCHASE',
            notes='Bulk order',
            recorded_by=self.user
        )
        self.assertEqual(log.quantity_change, 10)
        self.assertEqual(log.new_quantity, 15)  # 5 + 10
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 15)

    def test_create_log_negative_quantity_fails(self):
        with self.assertRaises(Exception):
            InventoryLogService.create_log(
                product=self.product,
                quantity_change=-10,  # would go negative (5-10 = -5)
                reason='SALE'
            )

    def test_get_logs_by_product(self):
        InventoryLog.objects.create(product=self.product, quantity_change=5, new_quantity=10, reason='PURCHASE')
        InventoryLog.objects.create(product=self.product, quantity_change=-2, new_quantity=8, reason='SALE')
        logs = InventoryLogService.get_logs_by_product(self.product.id)
        self.assertEqual(logs.count(), 2)

    def test_get_low_stock_products(self):
        low_product = Product.objects.create(
            name="Low Stock", category=self.category, price=10, stock_quantity=5
        )
        normal_product = Product.objects.create(
            name="Normal", category=self.category, price=20, stock_quantity=20
        )
        low = InventoryLogService.get_low_stock_products(threshold=10)
        self.assertIn(low_product, low)
        self.assertNotIn(normal_product, low)


class InventoryLogSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="staff3", email="staff3@example.com", password="test")
        self.category = Category.objects.create(name=ProductCategory.SNACKS)
        self.product = Product.objects.create(
            name="Chips",
            category=self.category,
            price=Decimal('45.00'),
            stock_quantity=20
        )

    def test_create_serializer_valid(self):
        data = {
            "product_id": self.product.id,
            "quantity_change": 10,
            "reason": "PURCHASE",
            "notes": "Restock",
            "recorded_by_id": self.user.id
        }
        serializer = InventoryLogCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        log = serializer.save()
        self.assertEqual(log.product, self.product)

    def test_update_serializer(self):
        log = InventoryLog.objects.create(
            product=self.product, quantity_change=5, new_quantity=25, reason='PURCHASE', notes='Original'
        )
        data = {"notes": "Updated notes"}
        serializer = InventoryLogUpdateSerializer(log, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.notes, "Updated notes")

    def test_display_serializer(self):
        log = InventoryLog.objects.create(
            product=self.product, quantity_change=10, new_quantity=30, reason='PURCHASE'
        )
        serializer = InventoryLogDisplaySerializer(log)
        self.assertEqual(serializer.data["product"]["id"], self.product.id)
        self.assertEqual(serializer.data["quantity_change"], 10)