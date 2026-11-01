from datetime import datetime, time, timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView, View

from accounts.mixins import RoleRequiredMixin
from accounts.models import User
from bookings.models import Booking
from complaints.models import Complaint
from leave_management.models import LeaveRequest
from notices.models import Notice
from rooms.models import Room
from students.models import Student
from visitors.models import Visitor

from .forms import HostelEventForm
from .models import HostelEvent


def redirect_to_role_dashboard(user):
    if user.role == "ADMIN":
        return redirect("dashboard:admin_dashboard")
    if user.role == "WARDEN":
        return redirect("dashboard:warden_dashboard")
    student = Student.objects.filter(user=user).select_related("room").first()
    if not student or not student.room:
        return redirect("accounts:login")
    return redirect("dashboard:student_dashboard")


def get_calendar_context(selected_date_str=None, user=None):
    """
    Builds weekly calendar days, daily event counts, and events for the selected date.
    Integrates recurring daily events (e.g. Community dinner) dynamically.
    Filters out WARDEN_ONLY events for STUDENTS.
    """
    today = timezone.localdate()
    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
        except ValueError:
            selected_date = today
    else:
        selected_date = today

    start_of_week = selected_date - timedelta(days=selected_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    # Base queryset with audience filtering if user is student
    events_qs = HostelEvent.objects.all()
    if user and getattr(user, "role", None) == "STUDENT":
        events_qs = events_qs.filter(audience=HostelEvent.Audience.ALL)

    # Specific events for this week
    week_events = list(
        events_qs.filter(
            is_recurring_daily=False,
            event_date__gte=start_of_week,
            event_date__lte=end_of_week,
        )
    )
    daily_recurring = list(events_qs.filter(is_recurring_daily=True))

    week_days = []
    labels = ["M", "T", "W", "T", "F", "S", "S"]
    for i in range(7):
        day_date = start_of_week + timedelta(days=i)
        has_specific = any(ev.event_date == day_date for ev in week_events)
        specific_count = sum(1 for ev in week_events if ev.event_date == day_date)

        week_days.append({
            "label": labels[i],
            "day_number": day_date.day,
            "date": day_date,
            "date_str": day_date.strftime("%Y-%m-%d"),
            "is_today": day_date == today,
            "is_selected": day_date == selected_date,
            "has_event": has_specific,  # Only indicate extra scheduled events
            "event_count": specific_count,
        })

    # Events on the selected day: specific events + daily recurring
    selected_day_events = list(
        events_qs.filter(is_recurring_daily=False, event_date=selected_date)
    )
    # Include recurring events as virtual instances for that day
    for rec in daily_recurring:
        selected_day_events.append(rec)
    selected_day_events.sort(key=lambda ev: ev.event_time)

    # Next upcoming event from now
    now_time = timezone.localtime().time()
    next_event = None
    for ev in selected_day_events:
        if selected_date > today or (selected_date == today and ev.event_time >= now_time):
            next_event = ev
            break
    if not next_event and selected_day_events:
        next_event = selected_day_events[0]

    return {
        "today": today,
        "selected_date": selected_date,
        "selected_date_str": selected_date.strftime("%Y-%m-%d"),
        "calendar_week_days": week_days,
        "calendar_month_year": selected_date.strftime("%B %Y"),
        "calendar_current_month": selected_date.strftime("%B"),
        "selected_day_events": selected_day_events,
        "next_event": next_event,
        "prev_week_str": (start_of_week - timedelta(days=7)).strftime("%Y-%m-%d"),
        "next_week_str": (start_of_week + timedelta(days=7)).strftime("%Y-%m-%d"),
    }


class CalendarDayEventsApiView(RoleRequiredMixin, View):
    """
    JSON API for dynamic date switching on dashboards without full page reloads.
    """
    allowed_roles = ("ADMIN", "WARDEN", "STUDENT")

    def get(self, request, *args, **kwargs):
        date_str = request.GET.get("date")
        ctx = get_calendar_context(date_str, user=request.user)
        events_data = []
        for ev in ctx["selected_day_events"]:
            events_data.append({
                "id": ev.pk,
                "title": ev.title,
                "event_type": ev.event_type,
                "event_type_display": ev.get_event_type_display(),
                "audience": ev.audience,
                "audience_display": ev.get_audience_display(),
                "time": ev.formatted_time_range,
                "start_time": ev.event_time.strftime("%I:%M %p").lstrip("0"),
                "end_time": ev.end_time.strftime("%I:%M %p").lstrip("0") if ev.end_time else "",
                "location": ev.location,
                "description": ev.description,
                "is_recurring_daily": ev.is_recurring_daily,
                "created_by": ev.created_by.get_full_name() or ev.created_by.username if ev.created_by else "",
            })
        next_event_data = None
        if ctx["next_event"]:
            ne = ctx["next_event"]
            next_event_data = {
                "id": ne.pk,
                "title": ne.title,
                "event_type": ne.event_type,
                "event_type_display": ne.get_event_type_display(),
                "audience": ne.audience,
                "audience_display": ne.get_audience_display(),
                "time": ne.formatted_time_range,
                "start_time": ne.event_time.strftime("%I:%M %p").lstrip("0"),
                "end_time": ne.end_time.strftime("%I:%M %p").lstrip("0") if ne.end_time else "",
                "location": ne.location,
                "description": ne.description,
                "is_recurring_daily": ne.is_recurring_daily,
            }
        return JsonResponse({
            "is_admin": request.user.role == "ADMIN",
            "is_student": request.user.role == "STUDENT",
            "today_str": ctx["today"].strftime("%Y-%m-%d"),
            "selected_date_str": ctx["selected_date_str"],
            "selected_date_formatted": ctx["selected_date"].strftime("%a, %d %b"),
            "selected_date_full": ctx["selected_date"].strftime("%A, %d %B %Y"),
            "calendar_month_year": ctx["calendar_month_year"],
            "prev_week_str": ctx["prev_week_str"],
            "next_week_str": ctx["next_week_str"],
            "week_days": [
                {
                    "label": d["label"],
                    "day_number": d["day_number"],
                    "date_str": d["date_str"],
                    "is_today": d["is_today"],
                    "is_selected": d["is_selected"],
                    "has_event": d["has_event"],
                    "event_count": d["event_count"],
                }
                for d in ctx["calendar_week_days"]
            ],
            "next_event": next_event_data,
            "events": events_data,
        })


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
        growth_items = []
        for i, month in enumerate(months):
            cnt = monthly_counts.get(month.year * 100 + month.month, 0)
            h = max(8, round(cnt * 100 / max_count))
            x = i * 120
            y = 150 - round((h / 100.0) * 115)
            growth_items.append({
                "label": month.strftime("%b"),
                "count": cnt,
                "height": h,
                "x": x,
                "y": y,
            })
        context["resident_growth"] = growth_items

        line_path_parts = [f"M {growth_items[0]['x']} {growth_items[0]['y']}"]
        for i in range(len(growth_items) - 1):
            p0 = growth_items[i]
            p1 = growth_items[i + 1]
            cx = (p0["x"] + p1["x"]) / 2
            line_path_parts.append(f"C {cx} {p0['y']}, {cx} {p1['y']}, {p1['x']} {p1['y']}")
        context["chart_line_path"] = " ".join(line_path_parts)
        context["chart_fill_path"] = f"M 0 180 L 0 {growth_items[0]['y']} " + " ".join(line_path_parts[1:]) + " L 600 180 Z"

        # Add calendar context for Admin as well
        selected_date_str = self.request.GET.get("date")
        context.update(get_calendar_context(selected_date_str, user=self.request.user))
        context["upcoming_events"] = HostelEvent.objects.all().order_by("is_recurring_daily", "event_date", "event_time")[:5]
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
        selected_date_str = self.request.GET.get("date")
        context.update(get_calendar_context(selected_date_str, user=self.request.user))
        return context


class StudentDashboardView(RoleRequiredMixin, TemplateView):
    template_name = "dashboard/student_dashboard.html"
    allowed_roles = ("STUDENT",)

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == "STUDENT":
            if not request.user.is_active:
                from django.contrib.auth import logout
                logout(request)
                messages.error(
                    request,
                    "Your hostel residency has been concluded or your account has been deactivated by an administrator. Please contact the hostel office.",
                )
                return redirect("accounts:login")

            student = Student.objects.filter(user=request.user).select_related("room").first()
            if not student or not student.room:
                from django.contrib.auth import logout
                logout(request)
                messages.warning(
                    request,
                    "Your registration is pending administrator approval and room allocation. You will be able to access your dashboard once approved and assigned a room.",
                )
                return redirect("accounts:login")
        return super().dispatch(request, *args, **kwargs)

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
        context["announcements"] = Notice.objects.exclude(
            title__startswith="[Warden Only]"
        ).exclude(body__startswith="[Warden Only]").select_related("created_by")[:3]
        context["recent_bookings"] = student.bookings.select_related("room")[:3] if student else []
        context["recent_leaves"] = student.leave_requests.all()[:3] if student else []
        context["recent_complaints"] = student.complaints.all()[:3] if student else []

        selected_date_str = self.request.GET.get("date")
        context.update(get_calendar_context(selected_date_str, user=self.request.user))

        profile_values = [
            self.request.user.first_name, self.request.user.last_name,
            self.request.user.email, self.request.user.phone_number,
            student.roll_number if student else "", student.course if student else "",
            student.emergency_contact if student else "",
        ]
        context["profile_completion"] = round(100 * sum(bool(value) for value in profile_values) / len(profile_values))
        return context


# =========================================================================
# Event Management Views (Admin has full permissions; Warden & Student read)
# =========================================================================

class EventListView(RoleRequiredMixin, ListView):
    """
    Events list view visible to all authenticated roles (Admin, Warden, Student).
    Admin sees creation, edit, and delete controls.
    """
    model = HostelEvent
    template_name = "dashboard/event_list.html"
    context_object_name = "events"
    allowed_roles = ("ADMIN", "WARDEN", "STUDENT")

    def get_queryset(self):
        query = self.request.GET.get("q", "").strip()
        qs = HostelEvent.objects.all().order_by("is_recurring_daily", "event_date", "event_time")
        if self.request.user.role == "STUDENT":
            qs = qs.filter(audience=HostelEvent.Audience.ALL)
        if query:
            qs = qs.filter(
                Q(title__icontains=query)
                | Q(location__icontains=query)
                | Q(description__icontains=query)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_date_str = self.request.GET.get("date")
        context.update(get_calendar_context(selected_date_str, user=self.request.user))
        return context


class EventCreateView(RoleRequiredMixin, CreateView):
    """
    Only ADMIN can create new events.
    """
    model = HostelEvent
    form_class = HostelEventForm
    template_name = "dashboard/event_form.html"
    allowed_roles = ("ADMIN",)

    def get_initial(self):
        initial = super().get_initial()
        date_str = self.request.GET.get("date")
        if date_str:
            try:
                parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                initial["event_date"] = parsed_date
            except (ValueError, TypeError):
                pass
        return initial

    def get_cancel_url(self):
        # 1. Check POST body first (persisted from previous form render)
        return_to = self.request.POST.get("return_to") or self.request.GET.get("return_to")
        if return_to and not any(kw in return_to for kw in ["/events/create", "/edit/", "/delete/"]):
            return return_to
        # 2. Check Referer header if it's not the form page itself
        ref = self.request.META.get("HTTP_REFERER")
        if ref and not any(kw in ref for kw in ["/events/create", "/edit/", "/delete/"]):
            return ref
        # 3. Default to events list with selected date
        date_str = self.request.GET.get("date") or self.request.POST.get("event_date")
        if date_str:
            return f"{reverse_lazy('dashboard:event_list')}?date={date_str}"
        return reverse_lazy("dashboard:event_list")

    def get_success_url(self):
        return self.get_cancel_url()

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Event '{form.instance.title}' created successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = "Create New Hostel Event"
        context["submit_label"] = "Publish Event"
        context["cancel_url"] = self.get_cancel_url()
        return context


class EventUpdateView(RoleRequiredMixin, UpdateView):
    """
    Only ADMIN can edit events (including recurring Community Dinner).
    """
    model = HostelEvent
    form_class = HostelEventForm
    template_name = "dashboard/event_form.html"
    allowed_roles = ("ADMIN",)

    def get_initial(self):
        initial = super().get_initial()
        date_str = self.request.GET.get("date")
        if date_str:
            try:
                parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                initial["event_date"] = parsed_date
            except (ValueError, TypeError):
                pass
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        date_str = self.request.GET.get("date")
        if date_str and not form.is_bound:
            try:
                parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                form.initial["event_date"] = parsed_date
                form.fields["event_date"].initial = parsed_date
            except (ValueError, TypeError):
                pass
        return form

    def get_cancel_url(self):
        # 1. Check POST body first
        return_to = self.request.POST.get("return_to") or self.request.GET.get("return_to")
        if return_to and not any(kw in return_to for kw in ["/events/create", "/edit/", "/delete/"]):
            return return_to
        # 2. Check Referer header if not the form itself
        ref = self.request.META.get("HTTP_REFERER")
        if ref and not any(kw in ref for kw in ["/events/create", "/edit/", "/delete/"]):
            return ref
        # 3. Default to events list with selected date
        date_str = self.request.GET.get("date")
        if date_str:
            return f"{reverse_lazy('dashboard:event_list')}?date={date_str}"
        if self.object.event_date:
            return f"{reverse_lazy('dashboard:event_list')}?date={self.object.event_date.strftime('%Y-%m-%d')}"
        return reverse_lazy("dashboard:event_list")

    def get_success_url(self):
        return self.get_cancel_url()

    def form_valid(self, form):
        messages.success(self.request, f"Event '{form.instance.title}' updated successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = f"Edit Event: {self.object.title}"
        context["submit_label"] = "Save Changes"
        context["cancel_url"] = self.get_cancel_url()
        return context


class EventDeleteView(RoleRequiredMixin, DeleteView):
    """
    Only ADMIN can delete events.
    """
    model = HostelEvent
    template_name = "dashboard/event_confirm_delete.html"
    allowed_roles = ("ADMIN",)

    def get_cancel_url(self):
        return_to = self.request.GET.get("return_to")
        if return_to:
            return return_to
        ref = self.request.META.get("HTTP_REFERER")
        if ref and ("events" in ref or "dashboard" in ref):
            return ref
        date_str = self.request.GET.get("date")
        if date_str:
            return f"{reverse_lazy('dashboard:event_list')}?date={date_str}"
        obj = self.get_object()
        if obj.event_date:
            return f"{reverse_lazy('dashboard:event_list')}?date={obj.event_date.strftime('%Y-%m-%d')}"
        return reverse_lazy("dashboard:event_list")

    def get_success_url(self):
        return self.get_cancel_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        date_str = self.request.GET.get("date")
        display_date = None
        if date_str:
            try:
                display_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                pass
        if not display_date:
            display_date = self.object.event_date
        context["display_date"] = display_date
        context["cancel_url"] = self.get_cancel_url()
        return context

    def delete(self, request, *args, **kwargs):
        event = self.get_object()
        title = event.title
        messages.success(request, f"Event '{title}' was deleted successfully.")
        return super().delete(request, *args, **kwargs)
