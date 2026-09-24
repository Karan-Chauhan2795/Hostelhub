from datetime import datetime, time, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.db.models import Count
from django.utils import timezone
from django.views.generic import TemplateView

from accounts.mixins import RoleRequiredMixin
from accounts.models import User
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
            {"title": "Total Wardens", "value": User.objects.filter(role=User.Role.WARDEN).count(), "change": "Current records"},
            {"title": "Occupied Rooms", "value": sum(room.occupied_count > 0 for room in rooms), "change": f"of {len(rooms)} rooms"},
            {"title": "Open Complaints", "value": Complaint.objects.exclude(status=Complaint.Status.RESOLVED).count(), "change": "Needs attention"},
            {"title": "Pending Bookings", "value": Booking.objects.filter(status=Booking.Status.PENDING).count(), "change": "Awaiting review"},
        ]
        context["students"] = Student.objects.select_related("user", "room").order_by("-created_at")[:3]
        context["rooms"] = rooms[:3]
        context["open_complaint_count"] = Complaint.objects.exclude(status=Complaint.Status.RESOLVED).count()
        context["available_room_count"] = sum(room.occupied_count < room.capacity for room in rooms)
        context["pending_booking_count"] = Booking.objects.filter(status=Booking.Status.PENDING).count()
        # This is intentionally calculated from resident records instead of a
        # decorative fixed chart.  It continues to work when the data changes.
        months = []
        today = timezone.localdate().replace(day=1)
        for offset in range(5, -1, -1):
            month = (today - timedelta(days=offset * 28)).replace(day=1)
            months.append(month)
        monthly_counts = {
            item["created_at__year"] * 100 + item["created_at__month"]: item["total"]
            for item in Student.objects.filter(
                created_at__gte=timezone.make_aware(datetime.combine(months[0], time.min))
            ).values(
                "created_at__year", "created_at__month"
            ).annotate(total=Count("id"))
        }
        max_count = max(monthly_counts.values(), default=0) or 1
        context["resident_growth"] = [
            {
                "label": month.strftime("%b"),
                "count": monthly_counts.get(month.year * 100 + month.month, 0),
                "height": max(8, round(monthly_counts.get(month.year * 100 + month.month, 0) * 100 / max_count)),
            }
            for month in months
        ]
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
        context["alerts"] = Notice.objects.select_related("created_by")[:3]
        context["active_visitors"] = Visitor.objects.filter(check_out__isnull=True).count()
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
        context["announcements"] = Notice.objects.all()[:3]
        context["recent_bookings"] = student.bookings.select_related("room")[:3] if student else []
        context["recent_leaves"] = student.leave_requests.all()[:3] if student else []
        context["recent_complaints"] = student.complaints.all()[:3] if student else []
        context["today"] = timezone.localdate()
        profile_values = [
            self.request.user.first_name, self.request.user.last_name,
            self.request.user.email, self.request.user.phone_number,
            student.roll_number if student else "", student.course if student else "",
            student.emergency_contact if student else "",
        ]
        context["profile_completion"] = round(100 * sum(bool(value) for value in profile_values) / len(profile_values))
        return context
