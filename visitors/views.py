from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from accounts.mixins import RoleRequiredMixin
from .forms import VisitorForm
from .models import Visitor


class VisitorListView(RoleRequiredMixin, ListView):
    model = Visitor
    allowed_roles = ("ADMIN", "WARDEN", "STUDENT")
    paginate_by = 10

    def get_template_names(self):
        if getattr(self.request.user, "role", None) == "STUDENT":
            return ["visitors/student_visitor_list.html"]
        return ["visitors/visitor_list.html"]

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, "role", None)

        if role == "STUDENT":
            # Security filter: Students can strictly see only their own visitor logs
            student_profile = getattr(user, "student_profile", None)
            if not student_profile:
                return Visitor.objects.none()
            qs = Visitor.objects.filter(student=student_profile).select_related("student__user", "student__room")
        else:
            # ADMIN and WARDEN see all visitors
            qs = Visitor.objects.select_related("student__user", "student__room")

        q = self.request.GET.get("q")
        if q:
            from django.db.models import Q
            filter_q = (
                Q(name__icontains=q)
                | Q(relation__icontains=q)
                | Q(purpose__icontains=q)
                | Q(phone__icontains=q)
            )
            if role != "STUDENT":
                filter_q |= (
                    Q(student__user__first_name__icontains=q)
                    | Q(student__user__last_name__icontains=q)
                    | Q(student__user__username__icontains=q)
                    | Q(student__roll_number__icontains=q)
                    | Q(student__room__number__icontains=q)
                )
            qs = qs.filter(filter_q)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["is_admin"] = getattr(user, "role", None) == "ADMIN"
        context["is_warden"] = getattr(user, "role", None) == "WARDEN"
        context["is_student"] = getattr(user, "role", None) == "STUDENT"
        return context


class VisitorCreateView(RoleRequiredMixin, CreateView):
    form_class = VisitorForm
    template_name = "visitors/visitor_create.html"
    success_url = reverse_lazy("visitors:visitor_list")
    allowed_roles = ("ADMIN", "WARDEN")

    def form_valid(self, form):
        messages.success(self.request, "Visitor successfully checked in.")
        return super().form_valid(form)


class VisitorUpdateView(RoleRequiredMixin, UpdateView):
    model = Visitor
    form_class = VisitorForm
    template_name = "visitors/visitor_edit.html"
    success_url = reverse_lazy("visitors:visitor_list")
    # STRICT ACCESS CONTROL: Only ADMIN can edit visitor records after adding
    allowed_roles = ("ADMIN",)

    def form_valid(self, form):
        messages.success(self.request, "Visitor information updated successfully.")
        return super().form_valid(form)


class VisitorHistoryView(VisitorListView):
    template_name = "visitors/visitor_history.html"
