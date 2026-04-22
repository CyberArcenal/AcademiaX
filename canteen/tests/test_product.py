from django.test import TestCase
from decimal import Decimal
from canteen.models import Category, Product
from canteen.services.product import ProductService
from canteen.serializers.product import (
    ProductCreateSerializer,
    ProductUpdateSerializer,
    ProductDisplaySerializer,
)
from common.enums.canteen import ProductCategory


class ProductModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name=ProductCategory.RICE_MEAL)

    def test_create_product(self):
        product = Product.objects.create(
            name="Chicken Rice",
            category=self.category,
            price=Decimal('120.00'),
            cost=Decimal('80.00'),
            stock_quantity=50,
            is_available=True
        )
        self.assertEqual(product.name, "Chicken Rice")
        self.assertEqual(product.price, Decimal('120.00'))
        self.assertEqual(product.stock_quantity, 50)

    def test_str_method(self):
        product = Product.objects.create(name="Burger", category=self.category, price=Decimal('99.00'))
        self.assertEqual(str(product), "Burger - ₱99.00")


class ProductServiceTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name=ProductCategory.SNACKS)

    def test_create_product(self):
        product = ProductService.create_product(
            name="Fries",
            category=self.category,
            price=Decimal('50.00'),
            cost=Decimal('25.00'),
            stock_quantity=100
        )
        self.assertEqual(product.name, "Fries")
        self.assertEqual(product.price, Decimal('50.00'))

    def test_get_products_by_category(self):
        Product.objects.create(name="Product A", category=self.category, price=10)
        Product.objects.create(name="Product B", category=self.category, price=20)
        products = ProductService.get_products_by_category(self.category.id)
        self.assertEqual(products.count(), 2)

    def test_update_stock(self):
        product = Product.objects.create(name="Soda", category=self.category, price=15, stock_quantity=10)
        updated = ProductService.update_stock(product, -3)
        self.assertEqual(updated.stock_quantity, 7)
        with self.assertRaises(Exception):
            ProductService.update_stock(product, -10)  # would go negative

    def test_check_availability(self):
        product = Product.objects.create(name="Chips", category=self.category, price=10, stock_quantity=5, is_available=True)
        self.assertTrue(ProductService.check_availability(product, 3))
        self.assertFalse(ProductService.check_availability(product, 10))

    def test_search_products(self):
        Product.objects.create(name="Pizza", category=self.category, price=200)
        Product.objects.create(name="Pasta", category=self.category, price=150)
        results = ProductService.search_products("Piz")
        self.assertEqual(results.count(), 1)


class ProductSerializerTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name=ProductCategory.RICE_MEAL)

    def test_create_serializer_valid(self):
        data = {
            "name": "Adobo Rice",
            "category_id": self.category.id,
            "price": "130.00",
            "cost": "90.00",
            "stock_quantity": 30
        }
        serializer = ProductCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        product = serializer.save()
        self.assertEqual(product.category, self.category)

    def test_update_serializer(self):
        product = Product.objects.create(name="Old Name", category=self.category, price=100)
        data = {"name": "New Name", "price": "120.00"}
        serializer = ProductUpdateSerializer(product, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.name, "New Name")

    def test_display_serializer(self):
        product = Product.objects.create(name="Display Test", category=self.category, price=75)
        serializer = ProductDisplaySerializer(product)
        self.assertEqual(serializer.data["name"], "Display Test")
        self.assertEqual(serializer.data["category"]["id"], self.category.id)