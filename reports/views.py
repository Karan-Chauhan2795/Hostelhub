from django.views.generic import TemplateView


class ReportsDashboardView(TemplateView):
    template_name = "reports/reports_dashboard.html"


class StudentReportView(TemplateView):
    template_name = "reports/student_report.html"


class AttendanceReportView(TemplateView):
    template_name = "reports/attendance_report.html"


class RoomReportView(TemplateView):
    template_name = "reports/room_report.html"


class ComplaintReportView(TemplateView):
    template_name = "reports/complaint_report.html"
