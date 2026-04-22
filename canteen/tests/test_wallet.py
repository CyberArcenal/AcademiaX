from django.test import TestCase
from decimal import Decimal
from users.models import User
from canteen.models import Wallet, WalletTransaction
from canteen.services.wallet import WalletService, WalletTransactionService
from canteen.serializers.wallet import (
    WalletCreateSerializer,
    WalletDisplaySerializer,
    WalletTransactionCreateSerializer,
    WalletTransactionDisplaySerializer,
)


class WalletModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="student1", email="s1@example.com", password="test")

    def test_create_wallet(self):
        wallet = Wallet.objects.create(user=self.user, balance=Decimal('0'))
        self.assertEqual(wallet.user, self.user)
        self.assertEqual(wallet.balance, Decimal('0'))

    def test_str_method(self):
        wallet = Wallet.objects.create(user=self.user, balance=Decimal('150.00'))
        expected = f"{self.user} - ₱150.00"
        self.assertEqual(str(wallet), expected)


class WalletServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="student2", email="s2@example.com", password="test")
        self.wallet = Wallet.objects.create(user=self.user, balance=Decimal('0'))

    def test_create_wallet(self):
        new_user = User.objects.create_user(username="new", email="new@example.com", password="test")
        wallet = WalletService.create_wallet(new_user)
        self.assertEqual(wallet.user, new_user)
        self.assertEqual(wallet.balance, Decimal('0'))

    def test_get_wallet_by_user(self):
        fetched = WalletService.get_wallet_by_user(self.user.id)
        self.assertEqual(fetched, self.wallet)

    def test_add_balance(self):
        updated = WalletService.add_balance(self.wallet, Decimal('100.00'), reference="LOAD-001", remarks="Cash deposit")
        self.assertEqual(updated.balance, Decimal('100.00'))
        # Check transaction record
        tx = self.wallet.transactions.last()
        self.assertEqual(tx.amount, Decimal('100.00'))
        self.assertEqual(tx.transaction_type, 'LOAD')

    def test_deduct_balance(self):
        self.wallet.balance = Decimal('200.00')
        self.wallet.save()
        updated = WalletService.deduct_balance(self.wallet, Decimal('50.00'), reference="PURCHASE-001", remarks="Canteen purchase")
        self.assertEqual(updated.balance, Decimal('150.00'))
        tx = self.wallet.transactions.last()
        self.assertEqual(tx.amount, Decimal('50.00'))
        self.assertEqual(tx.transaction_type, 'DEDUCT')

    def test_deduct_insufficient_balance(self):
        self.wallet.balance = Decimal('10.00')
        self.wallet.save()
        with self.assertRaises(Exception):
            WalletService.deduct_balance(self.wallet, Decimal('50.00'))

    def test_get_transactions(self):
        WalletTransaction.objects.create(wallet=self.wallet, amount=100, transaction_type='LOAD')
        WalletTransaction.objects.create(wallet=self.wallet, amount=30, transaction_type='DEDUCT')
        txs = WalletService.get_transactions(self.wallet)
        self.assertEqual(txs.count(), 2)


class WalletTransactionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="student3", email="s3@example.com", password="test")
        self.wallet = Wallet.objects.create(user=self.user, balance=Decimal('0'))

    def test_create_transaction(self):
        tx = WalletTransaction.objects.create(
            wallet=self.wallet,
            amount=Decimal('200.00'),
            transaction_type='LOAD',
            reference="REF001",
            remarks="Initial load"
        )
        self.assertEqual(tx.wallet, self.wallet)
        self.assertEqual(tx.amount, Decimal('200.00'))
        self.assertEqual(tx.transaction_type, 'LOAD')


class WalletTransactionServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="student4", email="s4@example.com", password="test")
        self.wallet = Wallet.objects.create(user=self.user, balance=Decimal('0'))
        self.tx = WalletTransaction.objects.create(
            wallet=self.wallet, amount=100, transaction_type='LOAD', reference="LOAD123"
        )

    def test_get_transaction_by_id(self):
        fetched = WalletTransactionService.get_transaction_by_id(self.tx.id)
        self.assertEqual(fetched, self.tx)

    def test_get_transactions_by_user(self):
        txs = WalletTransactionService.get_transactions_by_user(self.user.id)
        self.assertEqual(txs.count(), 1)


class WalletSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="student5", email="s5@example.com", password="test")

    def test_create_serializer_valid(self):
        data = {"user_id": self.user.id}
        serializer = WalletCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        wallet = serializer.save()
        self.assertEqual(wallet.user, self.user)

    def test_display_serializer(self):
        wallet = Wallet.objects.create(user=self.user, balance=Decimal('250.00'))
        serializer = WalletDisplaySerializer(wallet)
        self.assertEqual(serializer.data["user"]["id"], self.user.id)
        self.assertEqual(serializer.data["balance"], "250.00")


class WalletTransactionSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="student6", email="s6@example.com", password="test")
        self.wallet = Wallet.objects.create(user=self.user, balance=Decimal('0'))

    def test_create_serializer_valid_load(self):
        data = {
            "wallet_id": self.wallet.id,
            "amount": "100.00",
            "transaction_type": "LOAD",
            "reference": "LOAD001",
            "remarks": "Deposit",
            "processed_by_id": self.user.id
        }
        serializer = WalletTransactionCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        # Note: create method will call WalletService.add_balance or deduct_balance
        tx = serializer.save()
        self.assertEqual(tx.wallet, self.wallet)
        self.assertEqual(tx.amount, Decimal('100.00'))

    def test_create_serializer_valid_deduct(self):
        # First add balance
        WalletService.add_balance(self.wallet, Decimal('200.00'))
        data = {
            "wallet_id": self.wallet.id,
            "amount": "50.00",
            "transaction_type": "DEDUCT",
            "reference": "DEDUCT001",
            "remarks": "Purchase"
        }
        serializer = WalletTransactionCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        tx = serializer.save()
        self.assertEqual(tx.amount, Decimal('50.00'))

    def test_display_serializer(self):
        tx = WalletTransaction.objects.create(
            wallet=self.wallet, amount=75, transaction_type='LOAD', reference='REF'
        )
        serializer = WalletTransactionDisplaySerializer(tx)
        self.assertEqual(serializer.data["wallet"]["id"], self.wallet.id)
        self.assertEqual(serializer.data["amount"], "75.00")