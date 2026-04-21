from django.urls import path
from timetable.views.time_slot import (
    TimeSlotListView,
    TimeSlotDetailView,
    TimeSlotReorderView,
)

urlpatterns = [
    path("time-slots/", TimeSlotListView.as_view(), name="time-slot-list"),
    path("time-slots/<int:slot_id>/", TimeSlotDetailView.as_view(), name="time-slot-detail"),
    path("academic-years/<int:academic_year_id>/time-slots/reorder/", TimeSlotReorderView.as_view(), name="time-slot-reorder"),
]

from timetable.views.schedule import (
    ScheduleListView,
    ScheduleDetailView,
)

urlpatterns += [
    path("schedules/", ScheduleListView.as_view(), name="schedule-list"),
    path("schedules/<int:schedule_id>/", ScheduleDetailView.as_view(), name="schedule-detail"),
]

from timetable.views.schedule_override import (
    ScheduleOverrideListView,
    ScheduleOverrideDetailView,
    ScheduleOverrideCancelView,
)

urlpatterns += [
    path("schedule-overrides/", ScheduleOverrideListView.as_view(), name="schedule-override-list"),
    path("schedule-overrides/<int:override_id>/", ScheduleOverrideDetailView.as_view(), name="schedule-override-detail"),
    path("schedule-overrides/<int:override_id>/cancel/", ScheduleOverrideCancelView.as_view(), name="schedule-override-cancel"),
]

from timetable.views.room_schedule import (
    RoomScheduleListView,
    RoomScheduleDetailView,
    RoomAvailabilityView,
)

urlpatterns += [
    path("room-schedules/", RoomScheduleListView.as_view(), name="room-schedule-list"),
    path("room-schedules/<int:room_schedule_id>/", RoomScheduleDetailView.as_view(), name="room-schedule-detail"),
    path("room-availability/", RoomAvailabilityView.as_view(), name="room-availability"),
]