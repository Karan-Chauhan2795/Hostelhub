from django.db.models import Count
from django.views.generic import TemplateView

from accounts.mixins import RoleRequiredMixin
from complaints.models import Complaint
from bookings.models import Booking
from rooms.models import Room
from students.models import Student


class AdminReportView(RoleRequiredMixin, TemplateView):
    allowed_roles = ("ADMIN",)


class ReportsDashboardView(AdminReportView):
    template_name = "reports/reports_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["summary"] = {
            "students": Student.objects.count(),
            "rooms": Room.objects.count(),
            "complaints": Complaint.objects.count(),
            "bookings": Booking.objects.count(),
        }
        return context


class StudentReportView(AdminReportView):
    template_name = "reports/student_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["students"] = Student.objects.select_related("user", "room")
        return context


class AttendanceReportView(AdminReportView):
    template_name = "reports/attendance_report.html"


class RoomReportView(AdminReportView):
    template_name = "reports/room_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["rooms"] = Room.objects.annotate(resident_count=Count("residents"))
        return context


class ComplaintReportView(AdminReportView):
    template_name = "reports/complaint_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["complaints"] = Complaint.objects.select_related("student__user")
        return context
