from django.urls import path
from canteen.views.category import CategoryListView, CategoryDetailView

urlpatterns = [
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path("categories/<int:category_id>/", CategoryDetailView.as_view(), name="category-detail"),
]

from canteen.views.product import ProductListView, ProductDetailView, ProductSearchView

urlpatterns += [
    path("products/", ProductListView.as_view(), name="product-list"),
    path("products/<int:product_id>/", ProductDetailView.as_view(), name="product-detail"),
    path("products/search/", ProductSearchView.as_view(), name="product-search"),
]

from canteen.views.order import OrderListView, OrderDetailView, OrderStatusUpdateView

urlpatterns += [
    path("orders/", OrderListView.as_view(), name="order-list"),
    path("orders/<int:order_id>/", OrderDetailView.as_view(), name="order-detail"),
    path("orders/<int:order_id>/status/", OrderStatusUpdateView.as_view(), name="order-status"),
]

from canteen.views.order_item import OrderItemListView, OrderItemDetailView

urlpatterns += [
    path("order-items/", OrderItemListView.as_view(), name="order-item-list"),
    path("order-items/<int:item_id>/", OrderItemDetailView.as_view(), name="order-item-detail"),
]

from canteen.views.inventory import (
    InventoryLogListView,
    InventoryLogDetailView,
    LowStockAlertView,
)

urlpatterns += [
    path("inventory-logs/", InventoryLogListView.as_view(), name="inventory-log-list"),
    path("inventory-logs/<int:log_id>/", InventoryLogDetailView.as_view(), name="inventory-log-detail"),
    path("inventory/low-stock/", LowStockAlertView.as_view(), name="low-stock-alert"),
]

from canteen.views.transaction import (
    PaymentTransactionListView,
    PaymentTransactionDetailView,
    DailySalesView,
)

urlpatterns += [
    path("transactions/", PaymentTransactionListView.as_view(), name="transaction-list"),
    path("transactions/<int:transaction_id>/", PaymentTransactionDetailView.as_view(), name="transaction-detail"),
    path("transactions/daily-sales/", DailySalesView.as_view(), name="daily-sales"),
]

from canteen.views.wallet import (
    WalletListView,
    WalletDetailView,
    MyWalletView,
    WalletLoadView,
    WalletDeductView,
    WalletTransactionListView,
    WalletTransactionDetailView,
)

urlpatterns += [
    path("wallets/", WalletListView.as_view(), name="wallet-list"),
    path("wallets/<int:wallet_id>/", WalletDetailView.as_view(), name="wallet-detail"),
    path("wallets/my/", MyWalletView.as_view(), name="my-wallet"),
    path("wallets/<int:wallet_id>/load/", WalletLoadView.as_view(), name="wallet-load"),
    path("wallets/<int:wallet_id>/deduct/", WalletDeductView.as_view(), name="wallet-deduct"),
    path("wallet-transactions/", WalletTransactionListView.as_view(), name="wallet-transaction-list"),
    path("wallet-transactions/<int:transaction_id>/", WalletTransactionDetailView.as_view(), name="wallet-transaction-detail"),
]