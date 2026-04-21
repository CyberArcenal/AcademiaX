from rest_framework import serializers
from library.models import BorrowTransaction
from .copy import BookCopyMinimalSerializer
from students.serializers.student import StudentMinimalSerializer
from users.serializers.user.minimal import UserMinimalSerializer


class BorrowTransactionMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for borrow transactions."""

    copy = BookCopyMinimalSerializer(read_only=True)
    borrower = StudentMinimalSerializer(read_only=True)

    class Meta:
        model = BorrowTransaction
        fields = ["id", "copy", "borrower", "borrow_date", "due_date", "status"]
        read_only_fields = fields


class BorrowTransactionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a borrow transaction."""

    copy_id = serializers.PrimaryKeyRelatedField(
        queryset=BookCopy.objects.all(), source="copy"
    )
    borrower_id = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(), source="borrower"
    )
    borrowed_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="borrowed_by"
    )

    class Meta:
        model = BorrowTransaction
        fields = ["copy_id", "borrower_id", "borrowed_by_id", "borrow_date", "due_date", "notes"]

    def create(self, validated_data) -> BorrowTransaction:
        from library.services.borrow import BorrowTransactionService

        return BorrowTransactionService.create_borrow(**validated_data)


class BorrowTransactionUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a borrow transaction (return, renew)."""

    class Meta:
        model = BorrowTransaction
        fields = ["return_date", "due_date", "status", "notes"]

    def update(self, instance, validated_data) -> BorrowTransaction:
        from library.services.borrow import BorrowTransactionService

        if 'return_date' in validated_data:
            return BorrowTransactionService.return_book(instance, validated_data['return_date'], validated_data.get('notes', ''))
        if 'due_date' in validated_data:
            return BorrowTransactionService.renew_borrow(instance, validated_data['due_date'])
        return BorrowTransactionService.update_borrow(instance, validated_data)


class BorrowTransactionDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a borrow transaction."""

    copy = BookCopyMinimalSerializer(read_only=True)
    borrower = StudentMinimalSerializer(read_only=True)
    borrowed_by = UserMinimalSerializer(read_only=True)

    class Meta:
        model = BorrowTransaction
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]