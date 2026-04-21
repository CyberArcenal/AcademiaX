# common/enums/reports.py
from django.db import models

class ReportType(models.TextChoices):
    REPORT_CARD = 'RC', 'Report Card'
    TRANSCRIPT = 'TR', 'Transcript of Records'
    ATTENDANCE_SUMMARY = 'AT', 'Attendance Summary'
    FINANCIAL_STATEMENT = 'FS', 'Financial Statement'
    GRADE_SHEET = 'GS', 'Grade Sheet'
    COLLECTION_REPORT = 'CR', 'Collection Report'
    ENROLLMENT_REPORT = 'ER', 'Enrollment Report'
    CUSTOM = 'CU', 'Custom Report'

class ReportFormat(models.TextChoices):
    PDF = 'PDF', 'PDF Document'
    EXCEL = 'XLSX', 'Excel Spreadsheet'
    CSV = 'CSV', 'CSV File'
    JSON = 'JSON', 'JSON Data'

class ReportStatus(models.TextChoices):
    PENDING = 'PND', 'Pending Generation'
    PROCESSING = 'PRC', 'Processing'
    COMPLETED = 'CMP', 'Completed'
    FAILED = 'FLD', 'Failed'