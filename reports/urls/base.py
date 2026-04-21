from django.urls import path
from reports.views.report import (
    ReportListView,
    ReportDetailView,
    ReportDownloadView,
)

urlpatterns = [
    path("reports/", ReportListView.as_view(), name="report-list"),
    path("reports/<int:report_id>/", ReportDetailView.as_view(), name="report-detail"),
    path("reports/<int:report_id>/download/", ReportDownloadView.as_view(), name="report-download"),
]

from reports.views.report_template import (
    ReportTemplateListView,
    ReportTemplateDetailView,
    ReportTemplateSetDefaultView,
)

urlpatterns += [
    path("report-templates/", ReportTemplateListView.as_view(), name="report-template-list"),
    path("report-templates/<int:template_id>/", ReportTemplateDetailView.as_view(), name="report-template-detail"),
    path("report-templates/<int:template_id>/set-default/", ReportTemplateSetDefaultView.as_view(), name="report-template-set-default"),
]

from reports.views.report_schedule import (
    ReportScheduleListView,
    ReportScheduleDetailView,
)

urlpatterns += [
    path("report-schedules/", ReportScheduleListView.as_view(), name="report-schedule-list"),
    path("report-schedules/<int:schedule_id>/", ReportScheduleDetailView.as_view(), name="report-schedule-detail"),
]

from reports.views.report_log import (
    ReportLogListView,
    ReportLogDetailView,
)

urlpatterns += [
    path("report-logs/", ReportLogListView.as_view(), name="report-log-list"),
    path("report-logs/<int:log_id>/", ReportLogDetailView.as_view(), name="report-log-detail"),
]