from django.urls import path
from library.views.author import AuthorListView, AuthorDetailView

urlpatterns = [
    path("authors/", AuthorListView.as_view(), name="author-list"),
    path("authors/<int:author_id>/", AuthorDetailView.as_view(), name="author-detail"),
]

from library.views.publisher import PublisherListView, PublisherDetailView

urlpatterns += [
    path("publishers/", PublisherListView.as_view(), name="publisher-list"),
    path("publishers/<int:publisher_id>/", PublisherDetailView.as_view(), name="publisher-detail"),
]

from library.views.book import BookListView, BookDetailView, BookSearchView

urlpatterns += [
    path("books/", BookListView.as_view(), name="book-list"),
    path("books/<int:book_id>/", BookDetailView.as_view(), name="book-detail"),
    path("books/search/", BookSearchView.as_view(), name="book-search"),
]

from library.views.copy import (
    BookCopyListView,
    BookCopyDetailView,
    BookCopyUpdateStatusView,
)

urlpatterns += [
    path("copies/", BookCopyListView.as_view(), name="copy-list"),
    path("copies/<int:copy_id>/", BookCopyDetailView.as_view(), name="copy-detail"),
    path("copies/<int:copy_id>/update-status/", BookCopyUpdateStatusView.as_view(), name="copy-update-status"),
]

from library.views.borrow import (
    BorrowTransactionListView,
    BorrowTransactionDetailView,
    BorrowTransactionReturnView,
    BorrowTransactionRenewView,
)

urlpatterns += [
    path("borrows/", BorrowTransactionListView.as_view(), name="borrow-list"),
    path("borrows/<int:borrow_id>/", BorrowTransactionDetailView.as_view(), name="borrow-detail"),
    path("borrows/<int:borrow_id>/return/", BorrowTransactionReturnView.as_view(), name="borrow-return"),
    path("borrows/<int:borrow_id>/renew/", BorrowTransactionRenewView.as_view(), name="borrow-renew"),
]

from library.views.fine import (
    FineListView,
    FineDetailView,
    FinePayView,
    FineWaiveView,
)

urlpatterns += [
    path("fines/", FineListView.as_view(), name="fine-list"),
    path("fines/<int:fine_id>/", FineDetailView.as_view(), name="fine-detail"),
    path("fines/<int:fine_id>/pay/", FinePayView.as_view(), name="fine-pay"),
    path("fines/<int:fine_id>/waive/", FineWaiveView.as_view(), name="fine-waive"),
]

from library.views.reservation import (
    ReservationListView,
    ReservationDetailView,
    ReservationCancelView,
    ReservationFulfillView,
)

urlpatterns += [
    path("reservations/", ReservationListView.as_view(), name="reservation-list"),
    path("reservations/<int:reservation_id>/", ReservationDetailView.as_view(), name="reservation-detail"),
    path("reservations/<int:reservation_id>/cancel/", ReservationCancelView.as_view(), name="reservation-cancel"),
    path("reservations/<int:reservation_id>/fulfill/", ReservationFulfillView.as_view(), name="reservation-fulfill"),
]