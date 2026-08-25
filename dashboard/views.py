from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import TemplateView

from accounts.mixins import RoleRequiredMixin
from bookings.models import Booking
from complaints.models import Complaint
from leave_management.models import LeaveRequest
from notices.models import Notice
from rooms.models import Room
from students.models import Student
from visitors.models import Visitor


def redirect_to_role_dashboard(user):
    if user.role == "ADMIN":
        return redirect("dashboard:admin_dashboard")
    if user.role == "WARDEN":
        return redirect("dashboard:warden_dashboard")
    return redirect("dashboard:student_dashboard")


class LandingPageView(TemplateView):
    template_name = "landing.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect_to_role_dashboard(request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["landing_page"] = True
        context["rooms"] = Room.objects.all()[:3]
        return context


class DashboardRedirectView(LoginRequiredMixin, TemplateView):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        return redirect_to_role_dashboard(request.user)


class AdminDashboardView(RoleRequiredMixin, TemplateView):
    template_name = "dashboard/admin_dashboard.html"
    allowed_roles = ("ADMIN",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rooms = list(Room.objects.all())
        context["stats"] = [
            {"title": "Total Residents", "value": Student.objects.count(), "change": "Current records"},
            {"title": "Occupied Rooms", "value": sum(room.occupied_count > 0 for room in rooms), "change": f"of {len(rooms)} rooms"},
            {"title": "Open Complaints", "value": Complaint.objects.exclude(status=Complaint.Status.RESOLVED).count(), "change": "Needs attention"},
            {"title": "Pending Bookings", "value": Booking.objects.filter(status=Booking.Status.PENDING).count(), "change": "Awaiting review"},
        ]
        context["students"] = Student.objects.select_related("user", "room")[:3]
        context["rooms"] = rooms[:3]
        context["open_complaint_count"] = Complaint.objects.exclude(status=Complaint.Status.RESOLVED).count()
        context["available_room_count"] = sum(room.occupied_count < room.capacity for room in rooms)
        context["pending_booking_count"] = Booking.objects.filter(status=Booking.Status.PENDING).count()
        return context


class WardenDashboardView(RoleRequiredMixin, TemplateView):
    template_name = "dashboard/warden_dashboard.html"
    allowed_roles = ("WARDEN",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stats"] = [
            {"title": "Pending Approvals", "value": LeaveRequest.objects.filter(status=LeaveRequest.Status.PENDING).count(), "change": "Leave requests"},
            {"title": "Room Issues", "value": Complaint.objects.exclude(status=Complaint.Status.RESOLVED).count(), "change": "Open complaints"},
            {"title": "Visitors Logged", "value": Visitor.objects.count(), "change": "Current log"},
            {"title": "Residents", "value": Student.objects.count(), "change": "Current records"},
        ]
        context["alerts"] = Notice.objects.values_list("title", flat=True)[:2]
        return context


class StudentDashboardView(RoleRequiredMixin, TemplateView):
    template_name = "dashboard/student_dashboard.html"
    allowed_roles = ("STUDENT",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = Student.objects.filter(user=self.request.user).select_related("room").first()
        context["student_room"] = student.room.number if student and student.room else "Not assigned"
        context["stats"] = [
            {"title": "Current Room", "value": student.room.number if student and student.room else "Not assigned", "change": student.room.get_room_type_display() if student and student.room else "Contact the warden"},
            {"title": "Complaints", "value": student.complaints.exclude(status=Complaint.Status.RESOLVED).count() if student else 0, "change": "Open requests"},
            {"title": "Leave Requests", "value": student.leave_requests.filter(status=LeaveRequest.Status.PENDING).count() if student else 0, "change": "Pending"},
            {"title": "Bookings", "value": student.bookings.exclude(status=Booking.Status.CANCELLED).count() if student else 0, "change": "Active requests"},
        ]
        context["announcements"] = Notice.objects.values_list("title", flat=True)[:3]
        return context
