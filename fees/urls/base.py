from django.urls import path
from fees.views.fee_structure import FeeStructureListView, FeeStructureDetailView

urlpatterns = [
    path("fee-structures/", FeeStructureListView.as_view(), name="fee-structure-list"),
    path("fee-structures/<int:fs_id>/", FeeStructureDetailView.as_view(), name="fee-structure-detail"),
]

from fees.views.fee_assessment import (
    FeeAssessmentListView,
    FeeAssessmentDetailView,
    FeeAssessmentMarkOverdueView,
)

urlpatterns += [
    path("fee-assessments/", FeeAssessmentListView.as_view(), name="fee-assessment-list"),
    path("fee-assessments/<int:assessment_id>/", FeeAssessmentDetailView.as_view(), name="fee-assessment-detail"),
    path("fee-assessments/mark-overdue/", FeeAssessmentMarkOverdueView.as_view(), name="fee-assessment-mark-overdue"),
]

from fees.views.payment import (
    PaymentListView,
    PaymentDetailView,
    PaymentVerifyView,
)

urlpatterns += [
    path("payments/", PaymentListView.as_view(), name="payment-list"),
    path("payments/<int:payment_id>/", PaymentDetailView.as_view(), name="payment-detail"),
    path("payments/<int:payment_id>/verify/", PaymentVerifyView.as_view(), name="payment-verify"),
]

from fees.views.discount import DiscountListView, DiscountDetailView

urlpatterns += [
    path("discounts/", DiscountListView.as_view(), name="discount-list"),
    path("discounts/<int:discount_id>/", DiscountDetailView.as_view(), name="discount-detail"),
]

from fees.views.scholarship import (
    ScholarshipListView,
    ScholarshipDetailView,
    ScholarshipRenewView,
)

urlpatterns += [
    path("scholarships/", ScholarshipListView.as_view(), name="scholarship-list"),
    path("scholarships/<int:scholarship_id>/", ScholarshipDetailView.as_view(), name="scholarship-detail"),
    path("scholarships/<int:scholarship_id>/renew/", ScholarshipRenewView.as_view(), name="scholarship-renew"),
]

from fees.views.collection import CollectionReportListView, CollectionReportDetailView

urlpatterns += [
    path("collection-reports/", CollectionReportListView.as_view(), name="collection-report-list"),
    path("collection-reports/<int:report_id>/", CollectionReportDetailView.as_view(), name="collection-report-detail"),
]