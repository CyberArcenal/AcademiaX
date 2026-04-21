import logging
from django.db import transaction

logger = logging.getLogger(__name__)


class OrderStateTransitionService:
    """Handles side effects of order state changes."""

    @staticmethod
    def handle_creation(order):
        """When a new order is created, log it."""
        logger.info(f"Order {order.order_number} created for user {order.user or order.student}")

    @staticmethod
    def handle_changes(instance, changes):
        if 'status' in changes:
            OrderStateTransitionService._handle_status_change(
                instance, changes['status']['old'], changes['status']['new']
            )

    @staticmethod
    def _handle_status_change(order, old_status, new_status):
        """Handle order status transitions."""
        from canteen.services.inventory import InventoryLogService
        from canteen.services.order_item import OrderItemService
        from communication.services.notification import NotificationService

        # When order is completed
        if new_status == 'CP' and old_status != 'CP':
            # Deduct inventory for each item
            for item in order.items.all():
                product = item.product
                product.stock_quantity -= item.quantity
                product.save()
                InventoryLogService.create_log(
                    product=product,
                    quantity_change=-item.quantity,
                    reason='SALE',
                    notes=f"Order {order.order_number} completed"
                )
            logger.info(f"Order {order.order_number} completed, inventory deducted")

            # Notify user (if user exists and has wallet)
            if order.user and order.user.parent_profile:
                # Could send notification via parent communication
                pass
            elif order.student and order.student.user:
                NotificationService.create_notification(
                    recipient=order.student.user,
                    title="Order Completed",
                    message=f"Your order #{order.order_number} is ready for pickup.",
                    notification_type='INFO'
                )
            logger.info(f"Notification sent for completed order {order.order_number}")

        # When order is cancelled
        if new_status == 'CN' and old_status != 'CN':
            # If already completed, restore stock (should not happen, but safeguard)
            if old_status == 'CP':
                for item in order.items.all():
                    product = item.product
                    product.stock_quantity += item.quantity
                    product.save()
                    InventoryLogService.create_log(
                        product=product,
                        quantity_change=item.quantity,
                        reason='ADJUSTMENT',
                        notes=f"Order {order.order_number} cancelled, stock restored"
                    )
                logger.info(f"Order {order.order_number} cancelled after completion, stock restored")
            # Notify user
            if order.student and order.student.user:
                NotificationService.create_notification(
                    recipient=order.student.user,
                    title="Order Cancelled",
                    message=f"Your order #{order.order_number} has been cancelled. Reason: {order.cancelled_reason}",
                    notification_type='ALERT'
                )
            logger.info(f"Order {order.order_number} cancelled, notification sent")