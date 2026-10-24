from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from accounts.mixins import RoleRequiredMixin
from .forms import RoomForm
from .models import Room


class RoomManagementView(RoleRequiredMixin, ListView):
    model = Room
    template_name = "rooms/room_management.html"
    allowed_roles = ("ADMIN", "WARDEN")
    paginate_by = 10

    def get_queryset(self):
        rooms = Room.objects.all()
        query = self.request.GET.get("q", "").strip()
        if query:
            from django.db.models import Q
            rooms = rooms.filter(Q(number__icontains=query) | Q(room_type__icontains=query))
        status = self.request.GET.get("status")
        if status == "VACANT":
            rooms = [room for room in rooms if room.occupied_count == 0]
        elif status == "AVAILABLE":
            rooms = [room for room in rooms if room.occupied_count < room.capacity]
        elif status == "OCCUPIED":
            rooms = [room for room in rooms if room.occupied_count >= room.capacity]
        return rooms


class RoomCreateView(RoleRequiredMixin, CreateView):
    template_name = "rooms/room_create.html"
    form_class = RoomForm
    success_url = reverse_lazy("rooms:room_management")
    allowed_roles = ("ADMIN", "WARDEN")

    def form_valid(self, form):
        messages.success(self.request, "Room added.")
        return super().form_valid(form)


class RoomUpdateView(RoleRequiredMixin, UpdateView):
    template_name = "rooms/room_update.html"
    form_class = RoomForm
    model = Room
    success_url = reverse_lazy("rooms:room_management")
    allowed_roles = ("ADMIN", "WARDEN")


import json
from decimal import Decimal, InvalidOperation
from django.http import JsonResponse
from django.views import View


class RoomAPIViewBase(View):
    allowed_staff_roles = ("ADMIN", "WARDEN")

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication credentials were not provided."}, status=401)
        return super().dispatch(request, *args, **kwargs)

    def is_staff(self, user):
        return getattr(user, "role", None) in self.allowed_staff_roles

    def serialize_room(self, room):
        return {
            "id": room.id,
            "number": room.number,
            "room_type": room.room_type,
            "room_type_display": room.get_room_type_display(),
            "capacity": room.capacity,
            "occupied_count": room.occupied_count,
            "status": room.status,
            "monthly_fee": str(room.monthly_fee),
            "created_at": room.created_at.isoformat() if room.created_at else None,
        }

    def parse_json_body(self, request):
        if request.content_type and "application/json" not in request.content_type:
            return None, JsonResponse({"error": "Content-Type must be application/json."}, status=415)
        try:
            body = request.body.decode("utf-8")
            if not body:
                return {}, None
            return json.loads(body), None
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None, JsonResponse({"error": "Malformed JSON body."}, status=400)

    def validate_and_extract_data(self, data, partial=False, current_room=None):
        errors = {}
        cleaned = {}

        if not partial and "number" not in data:
            errors["number"] = "This field is required."
        elif "number" in data:
            num = str(data["number"]).strip()
            if not num:
                errors["number"] = "Room number cannot be empty."
            elif len(num) > 20:
                errors["number"] = "Room number cannot exceed 20 characters."
            else:
                existing = Room.objects.filter(number__iexact=num)
                if current_room:
                    existing = existing.exclude(pk=current_room.pk)
                if existing.exists():
                    errors["number"] = "A room with this number already exists."
                else:
                    cleaned["number"] = num

        valid_types = [choice[0] for choice in Room.RoomType.choices]
        if not partial and "room_type" not in data:
            errors["room_type"] = "This field is required."
        elif "room_type" in data:
            rt = str(data["room_type"]).strip()
            if rt not in valid_types:
                errors["room_type"] = f"Invalid room type. Allowed: {valid_types}"
            else:
                cleaned["room_type"] = rt

        if not partial and "capacity" not in data:
            errors["capacity"] = "This field is required."
        elif "capacity" in data:
            try:
                cap = int(data["capacity"])
                if cap <= 0:
                    errors["capacity"] = "Capacity must be a positive integer."
                elif cap > 50:
                    errors["capacity"] = "Capacity cannot exceed 50."
                elif current_room and cap < current_room.occupied_count:
                    errors["capacity"] = f"Capacity cannot be less than currently occupied count ({current_room.occupied_count})."
                else:
                    cleaned["capacity"] = cap
            except (ValueError, TypeError):
                errors["capacity"] = "Capacity must be a valid integer."

        if not partial and "monthly_fee" not in data:
            errors["monthly_fee"] = "This field is required."
        elif "monthly_fee" in data:
            try:
                fee = Decimal(str(data["monthly_fee"]))
                if fee < Decimal("0"):
                    errors["monthly_fee"] = "Monthly fee cannot be negative."
                elif fee > Decimal("9999999.99"):
                    errors["monthly_fee"] = "Monthly fee exceeds maximum allowed limit."
                else:
                    cleaned["monthly_fee"] = fee
            except (InvalidOperation, TypeError, ValueError):
                errors["monthly_fee"] = "Monthly fee must be a valid decimal amount."

        return cleaned, errors


class RoomListCreateAPIView(RoomAPIViewBase):
    http_method_names = ["get", "post"]

    def get(self, request, *args, **kwargs):
        rooms = Room.objects.all()
        q = request.GET.get("q", "").strip()
        if q:
            from django.db.models import Q
            rooms = rooms.filter(Q(number__icontains=q) | Q(room_type__icontains=q))

        room_type = request.GET.get("room_type", "").strip()
        if room_type:
            rooms = rooms.filter(room_type=room_type)

        status_filter = request.GET.get("status", "").strip().upper()
        serialized = []
        for room in rooms:
            if status_filter == "VACANT" and room.occupied_count != 0:
                continue
            if status_filter == "AVAILABLE" and room.occupied_count >= room.capacity:
                continue
            if status_filter == "OCCUPIED" and room.occupied_count < room.capacity:
                continue
            serialized.append(self.serialize_room(room))

        return JsonResponse({"count": len(serialized), "rooms": serialized}, status=200)

    def post(self, request, *args, **kwargs):
        if not self.is_staff(request.user):
            return JsonResponse({"error": "You do not have permission to perform this action."}, status=403)

        payload, err_response = self.parse_json_body(request)
        if err_response:
            return err_response

        cleaned, errors = self.validate_and_extract_data(payload, partial=False)
        if errors:
            return JsonResponse({"errors": errors}, status=400)

        room = Room.objects.create(**cleaned)
        return JsonResponse(self.serialize_room(room), status=201)


class RoomDetailAPIView(RoomAPIViewBase):
    http_method_names = ["get", "put", "patch", "delete"]

    def get_room(self, pk):
        try:
            return Room.objects.get(pk=pk), None
        except Room.DoesNotExist:
            return None, JsonResponse({"error": "Room not found."}, status=404)

    def get(self, request, pk, *args, **kwargs):
        room, err = self.get_room(pk)
        if err:
            return err
        return JsonResponse(self.serialize_room(room), status=200)

    def put(self, request, pk, *args, **kwargs):
        if not self.is_staff(request.user):
            return JsonResponse({"error": "You do not have permission to perform this action."}, status=403)

        room, err = self.get_room(pk)
        if err:
            return err

        payload, err_response = self.parse_json_body(request)
        if err_response:
            return err_response

        cleaned, errors = self.validate_and_extract_data(payload, partial=False, current_room=room)
        if errors:
            return JsonResponse({"errors": errors}, status=400)

        for attr, value in cleaned.items():
            setattr(room, attr, value)
        room.save()
        return JsonResponse(self.serialize_room(room), status=200)

    def patch(self, request, pk, *args, **kwargs):
        if not self.is_staff(request.user):
            return JsonResponse({"error": "You do not have permission to perform this action."}, status=403)

        room, err = self.get_room(pk)
        if err:
            return err

        payload, err_response = self.parse_json_body(request)
        if err_response:
            return err_response

        if not payload:
            return JsonResponse({"error": "No fields provided to update."}, status=400)

        cleaned, errors = self.validate_and_extract_data(payload, partial=True, current_room=room)
        if errors:
            return JsonResponse({"errors": errors}, status=400)

        for attr, value in cleaned.items():
            setattr(room, attr, value)
        room.save()
        return JsonResponse(self.serialize_room(room), status=200)

    def delete(self, request, pk, *args, **kwargs):
        if not self.is_staff(request.user):
            return JsonResponse({"error": "You do not have permission to perform this action."}, status=403)

        room, err = self.get_room(pk)
        if err:
            return err

        if room.occupied_count > 0:
            return JsonResponse({"error": "Cannot delete room with allocated residents."}, status=400)

        if hasattr(room, "bookings") and room.bookings.filter(status="CONFIRMED").exists():
            return JsonResponse({"error": "Cannot delete room with confirmed bookings."}, status=400)

        room.delete()
        return JsonResponse({"message": "Room deleted successfully."}, status=200)

