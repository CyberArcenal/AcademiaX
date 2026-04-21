from django.urls import path
from facilities.views.building import BuildingListView, BuildingDetailView

urlpatterns = [
    path("buildings/", BuildingListView.as_view(), name="building-list"),
    path("buildings/<int:building_id>/", BuildingDetailView.as_view(), name="building-detail"),
]

from facilities.views.facility import FacilityListView, FacilityDetailView, FacilityAvailableView

urlpatterns += [
    path("facilities/", FacilityListView.as_view(), name="facility-list"),
    path("facilities/<int:facility_id>/", FacilityDetailView.as_view(), name="facility-detail"),
    path("facilities/available/", FacilityAvailableView.as_view(), name="facility-available"),
]

from facilities.views.equipment import (
    EquipmentListView,
    EquipmentDetailView,
    EquipmentUpdateStatusView,
)

urlpatterns += [
    path("equipment/", EquipmentListView.as_view(), name="equipment-list"),
    path("equipment/<int:equipment_id>/", EquipmentDetailView.as_view(), name="equipment-detail"),
    path("equipment/<int:equipment_id>/update-status/", EquipmentUpdateStatusView.as_view(), name="equipment-update-status"),
]

from facilities.views.maintenance import (
    MaintenanceRequestListView,
    MaintenanceRequestDetailView,
    MaintenanceRequestStatusUpdateView,
)

urlpatterns += [
    path("maintenance-requests/", MaintenanceRequestListView.as_view(), name="maintenance-list"),
    path("maintenance-requests/<int:request_id>/", MaintenanceRequestDetailView.as_view(), name="maintenance-detail"),
    path("maintenance-requests/<int:request_id>/update-status/", MaintenanceRequestStatusUpdateView.as_view(), name="maintenance-update-status"),
]

from facilities.views.reservation import (
    FacilityReservationListView,
    FacilityReservationDetailView,
    FacilityReservationApproveView,
    FacilityReservationRejectView,
    FacilityReservationCancelView,
)

urlpatterns += [
    path("reservations/", FacilityReservationListView.as_view(), name="reservation-list"),
    path("reservations/<int:reservation_id>/", FacilityReservationDetailView.as_view(), name="reservation-detail"),
    path("reservations/<int:reservation_id>/approve/", FacilityReservationApproveView.as_view(), name="reservation-approve"),
    path("reservations/<int:reservation_id>/reject/", FacilityReservationRejectView.as_view(), name="reservation-reject"),
    path("reservations/<int:reservation_id>/cancel/", FacilityReservationCancelView.as_view(), name="reservation-cancel"),
]

from facilities.views.usage_log import (
    FacilityUsageLogListView,
    FacilityUsageLogDetailView,
    FacilityUsageLogCheckoutView,
)

urlpatterns += [
    path("usage-logs/", FacilityUsageLogListView.as_view(), name="usage-log-list"),
    path("usage-logs/<int:log_id>/", FacilityUsageLogDetailView.as_view(), name="usage-log-detail"),
    path("usage-logs/<int:log_id>/checkout/", FacilityUsageLogCheckoutView.as_view(), name="usage-log-checkout"),
]