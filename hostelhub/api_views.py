from django.http import JsonResponse
from django.views import View

from accounts.mixins import RoleRequiredMixin
from rooms.models import Room
from students.models import Student
from complaints.models import Complaint
from bookings.models import Booking
from notices.models import Notice
from leave_management.models import LeaveRequest
from visitors.models import Visitor


class BaseAPIListView(View):
    """Base API view providing JSON data access for developer inspection and testing."""
    pass


class APIIndexView(BaseAPIListView):
    """Root /api/ endpoint listing all available API resources and summary counts."""

    def get(self, request, *args, **kwargs):
        return JsonResponse({
            "message": "HostelHub API Directory",
            "endpoints": {
                "api_index": "/api/",
                "rooms": "/api/rooms/ (or /rooms/api/)",
                "students": "/api/students/",
                "complaints": "/api/complaints/",
                "bookings": "/api/bookings/",
                "notices": "/api/notices/",
                "leave_requests": "/api/leave/",
                "visitors": "/api/visitors/",
            },
            "counts": {
                "rooms": Room.objects.count(),
                "students": Student.objects.count(),
                "complaints": Complaint.objects.count(),
                "bookings": Booking.objects.count(),
                "notices": Notice.objects.count(),
                "leave_requests": LeaveRequest.objects.count(),
                "visitors": Visitor.objects.count(),
            }
        }, status=200)


class StudentListAPIView(BaseAPIListView):
    """Returns JSON list of students."""

    def get(self, request, *args, **kwargs):
        queryset = Student.objects.select_related("user", "room").all()
        q = request.GET.get("q", "").strip()
        if q:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(roll_number__icontains=q)
                | Q(user__username__icontains=q)
                | Q(user__first_name__icontains=q)
                | Q(user__last_name__icontains=q)
                | Q(course__icontains=q)
            )

        data = [
            {
                "id": s.id,
                "roll_number": s.roll_number,
                "name": s.user.get_full_name() or s.user.username,
                "username": s.user.username,
                "email": s.user.email,
                "course": s.course,
                "room": s.room.number if s.room else None,
                "is_active": s.user.is_active,
                "emergency_contact": s.emergency_contact,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in queryset
        ]
        return JsonResponse({"count": len(data), "students": data}, status=200)


class ComplaintListAPIView(BaseAPIListView):
    """Returns JSON list of complaints."""

    def get(self, request, *args, **kwargs):
        queryset = Complaint.objects.select_related("student__user").all()
        if request.user.role == "STUDENT":
            queryset = queryset.filter(student__user=request.user)

        status_param = request.GET.get("status", "").strip()
        if status_param in Complaint.Status.values:
            queryset = queryset.filter(status=status_param)

        data = [
            {
                "id": c.id,
                "student": c.student.user.get_full_name() or c.student.user.username,
                "student_roll": c.student.roll_number,
                "subject": c.subject,
                "description": c.description,
                "status": c.status,
                "status_display": c.get_status_display(),
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            }
            for c in queryset
        ]
        return JsonResponse({"count": len(data), "complaints": data}, status=200)


class BookingListAPIView(BaseAPIListView):
    """Returns JSON list of room allocations / bookings."""

    def get(self, request, *args, **kwargs):
        queryset = Booking.objects.select_related("student__user", "room").all()
        if request.user.role == "STUDENT":
            queryset = queryset.filter(student__user=request.user)

        status_param = request.GET.get("status", "").strip()
        if status_param in Booking.Status.values:
            queryset = queryset.filter(status=status_param)

        data = [
            {
                "id": b.id,
                "student": b.student.user.get_full_name() or b.student.user.username,
                "student_roll": b.student.roll_number,
                "room": b.room.number,
                "status": b.status,
                "requested_at": b.requested_at.isoformat() if b.requested_at else None,
                "notes": b.notes,
            }
            for b in queryset
        ]
        return JsonResponse({"count": len(data), "bookings": data}, status=200)


class NoticeListAPIView(BaseAPIListView):
    """Returns JSON list of notices."""

    def get(self, request, *args, **kwargs):
        queryset = Notice.objects.select_related("created_by").all()
        if request.user.role == "STUDENT":
            queryset = [n for n in queryset if not n.is_warden_only]

        data = [
            {
                "id": n.id,
                "title": n.clean_display_title,
                "raw_title": n.title,
                "body": n.body,
                "is_warden_only": n.is_warden_only,
                "created_by": n.created_by.get_full_name() or n.created_by.username if n.created_by else "HostelHub",
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in queryset
        ]
        return JsonResponse({"count": len(data), "notices": data}, status=200)


class LeaveRequestListAPIView(BaseAPIListView):
    """Returns JSON list of leave requests."""

    def get(self, request, *args, **kwargs):
        queryset = LeaveRequest.objects.select_related("student__user").all()
        if request.user.role == "STUDENT":
            queryset = queryset.filter(student__user=request.user)

        data = [
            {
                "id": l.id,
                "student": l.student.user.get_full_name() or l.student.user.username,
                "student_roll": l.student.roll_number,
                "start_date": l.start_date.isoformat() if l.start_date else None,
                "end_date": l.end_date.isoformat() if l.end_date else None,
                "reason": l.reason,
                "status": l.status,
                "status_display": l.get_status_display(),
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in queryset
        ]
        return JsonResponse({"count": len(data), "leave_requests": data}, status=200)


class VisitorListAPIView(BaseAPIListView):
    """Returns JSON list of visitor logs."""

    def get(self, request, *args, **kwargs):
        queryset = Visitor.objects.select_related("student__user").all()
        data = [
            {
                "id": v.id,
                "name": v.name,
                "phone": v.phone,
                "student": v.student.user.get_full_name() or v.student.user.username,
                "purpose": v.purpose,
                "check_in": v.check_in.isoformat() if v.check_in else None,
                "check_out": v.check_out.isoformat() if v.check_out else None,
            }
            for v in queryset
        ]
        return JsonResponse({"count": len(data), "visitors": data}, status=200)
