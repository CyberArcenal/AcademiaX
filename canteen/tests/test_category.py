from django.test import TestCase
from canteen.models import Category
from canteen.services.category import CategoryService
from canteen.serializers.category import (
    CategoryCreateSerializer,
    CategoryUpdateSerializer,
    CategoryDisplaySerializer,
)
from common.enums.canteen import ProductCategory


class CategoryModelTest(TestCase):
    def test_create_category(self):
        category = Category.objects.create(
            name=ProductCategory.RICE_MEAL,
            display_order=1,
            description="Rice meals"
        )
        self.assertEqual(category.name, ProductCategory.RICE_MEAL)
        self.assertEqual(category.display_order, 1)

    def test_str_method(self):
        category = Category.objects.create(name=ProductCategory.DRINKS)
        self.assertEqual(str(category), "Drinks")


class CategoryServiceTest(TestCase):
    def test_create_category(self):
        category = CategoryService.create_category(
            name=ProductCategory.SNACKS,
            display_order=2
        )
        self.assertEqual(category.name, ProductCategory.SNACKS)

    def test_get_all_categories(self):
        Category.objects.create(name=ProductCategory.RICE_MEAL)
        Category.objects.create(name=ProductCategory.DRINKS)
        categories = CategoryService.get_all_categories()
        self.assertEqual(categories.count(), 2)

    def test_update_category(self):
        category = Category.objects.create(name=ProductCategory.SNACKS, display_order=1)
        updated = CategoryService.update_category(category, {"display_order": 5})
        self.assertEqual(updated.display_order, 5)

    def test_reorder_categories(self):
        c1 = Category.objects.create(name=ProductCategory.RICE_MEAL, display_order=1)
        c2 = Category.objects.create(name=ProductCategory.DRINKS, display_order=2)
        success = CategoryService.reorder_categories([c2.id, c1.id])
        self.assertTrue(success)
        c1.refresh_from_db()
        c2.refresh_from_db()
        self.assertEqual(c1.display_order, 2)
        self.assertEqual(c2.display_order, 1)


class CategorySerializerTest(TestCase):
    def test_create_serializer_valid(self):
        data = {
            "name": ProductCategory.SANDWICH,
            "display_order": 3
        }
        serializer = CategoryCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        category = serializer.save()
        self.assertEqual(category.name, ProductCategory.SANDWICH)

    def test_update_serializer(self):
        category = Category.objects.create(name=ProductCategory.RICE_MEAL)
        data = {"description": "New description", "display_order": 10}
        serializer = CategoryUpdateSerializer(category, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.description, "New description")

    def test_display_serializer(self):
        category = Category.objects.create(name=ProductCategory.DRINKS)
        serializer = CategoryDisplaySerializer(category)
        self.assertEqual(serializer.data["name"], ProductCategory.DRINKS)