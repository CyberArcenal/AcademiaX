from rest_framework import serializers
from canteen.models import Wallet, WalletTransaction
from users.serializers.user.minimal import UserMinimalSerializer


# Wallet serializers
class WalletMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for wallets."""

    user = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Wallet
        fields = ["id", "user", "balance"]
        read_only_fields = fields


class WalletCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a wallet (usually auto-created with user)."""

    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="user"
    )

    class Meta:
        model = Wallet
        fields = ["user_id"]

    def create(self, validated_data) -> Wallet:
        from canteen.services.wallet import WalletService

        return WalletService.create_wallet(**validated_data)


class WalletUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a wallet (balance is updated via transactions, not directly)."""

    class Meta:
        model = Wallet
        fields = []  # No direct updates, only via add/deduct methods

    def update(self, instance, validated_data) -> Wallet:
        # Not used directly; use WalletService methods
        return instance


class WalletDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a wallet."""

    user = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Wallet
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "balance"]


# WalletTransaction serializers
class WalletTransactionMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for wallet transactions."""

    class Meta:
        model = WalletTransaction
        fields = ["id", "amount", "transaction_type", "created_at"]
        read_only_fields = fields


class WalletTransactionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a wallet transaction (load/deduct)."""

    wallet_id = serializers.PrimaryKeyRelatedField(
        queryset=Wallet.objects.all(), source="wallet"
    )
    processed_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="processed_by", required=False, allow_null=True
    )

    class Meta:
        model = WalletTransaction
        fields = ["wallet_id", "amount", "transaction_type", "reference", "remarks", "processed_by_id"]

    def create(self, validated_data) -> WalletTransaction:
        from canteen.services.wallet import WalletService

        wallet = validated_data['wallet']
        amount = validated_data['amount']
        transaction_type = validated_data['transaction_type']
        if transaction_type == 'LOAD':
            WalletService.add_balance(wallet, amount, validated_data.get('reference', ''), validated_data.get('remarks', ''), validated_data.get('processed_by'))
        else:
            WalletService.deduct_balance(wallet, amount, validated_data.get('reference', ''), validated_data.get('remarks', ''), validated_data.get('processed_by'))
        # Return the last transaction
        return wallet.transactions.last()


class WalletTransactionUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a wallet transaction (only remarks)."""

    class Meta:
        model = WalletTransaction
        fields = ["remarks"]

    def update(self, instance, validated_data) -> WalletTransaction:
        instance.remarks = validated_data.get('remarks', instance.remarks)
        instance.save()
        return instance


class WalletTransactionDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a wallet transaction."""

    wallet = WalletMinimalSerializer(read_only=True)
    processed_by = UserMinimalSerializer(read_only=True)

    class Meta:
        model = WalletTransaction
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]