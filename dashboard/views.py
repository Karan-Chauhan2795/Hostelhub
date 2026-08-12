from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import TemplateView

from accounts.mixins import RoleRequiredMixin


def redirect_to_role_dashboard(user):
    if user.role == "ADMIN":
        return redirect("dashboard:admin_dashboard")
    if user.role == "WARDEN":
        return redirect("dashboard:warden_dashboard")
    return redirect("dashboard:student_dashboard")


class LandingPageView(TemplateView):
    """Public marketing page for HostelHub."""

    template_name = "landing.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect_to_role_dashboard(request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["landing_page"] = True
        context["rooms"] = [
            {"name": "Twin Studio", "price": "₹8,500", "image": "https://images.unsplash.com/photo-1631049307264-da0ec9d70304?auto=format&fit=crop&w=900&q=85", "features": "2 residents · Ensuite bath"},
            {"name": "Premium Single", "price": "₹12,000", "image": "https://images.unsplash.com/photo-1616486338812-3dadae4b4ace?auto=format&fit=crop&w=900&q=85", "features": "Private room · Study-ready"},
            {"name": "Four-Bed Suite", "price": "₹6,500", "image": "https://images.unsplash.com/photo-1598928506311-c55ded91a20c?auto=format&fit=crop&w=900&q=85", "features": "4 residents · Best value"},
        ]
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
        context["stats"] = [
            {"title": "Total Residents", "value": "248", "change": "+12%"},
            {"title": "Occupied Rooms", "value": "196", "change": "+8%"},
            {"title": "Open Complaints", "value": "11", "change": "-3"},
            {"title": "Attendance Today", "value": "94%", "change": "+2%"},
        ]
        context["students"] = [
            {"name": "Aarav Mehta", "room": "A-101", "status": "Active"},
            {"name": "Sneha Verma", "room": "B-204", "status": "Pending Fee"},
            {"name": "Rajat Kumar", "room": "C-305", "status": "Active"},
        ]
        context["rooms"] = [
            {"number": "A-101", "occupancy": "2/2"},
            {"number": "B-204", "occupancy": "1/2"},
            {"number": "C-305", "occupancy": "2/2"},
        ]
        return context


class WardenDashboardView(RoleRequiredMixin, TemplateView):
    template_name = "dashboard/warden_dashboard.html"
    allowed_roles = ("WARDEN",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stats"] = [
            {"title": "Night Checks", "value": "18", "change": "+4"},
            {"title": "Pending Approvals", "value": "5", "change": "+1"},
            {"title": "Room Issues", "value": "3", "change": "-1"},
            {"title": "Visitors Today", "value": "9", "change": "+2"},
        ]
        context["alerts"] = [
            "Hostel curfew reminder sent to all residents.",
            "Maintenance request for block C is under review.",
        ]
        return context


class StudentDashboardView(RoleRequiredMixin, TemplateView):
    template_name = "dashboard/student_dashboard.html"
    allowed_roles = ("STUDENT",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stats"] = [
            {"title": "Hostel Fee", "value": "Paid", "change": "Up to date"},
            {"title": "Current Room", "value": "B-204", "change": "Shared"},
            {"title": "Complaints", "value": "1", "change": "In review"},
            {"title": "Leave Requests", "value": "0", "change": "No pending"},
        ]
        context["announcements"] = [
            "Mess timings updated for the weekend.",
            "Library access extended till 10 PM.",
        ]
        return context
