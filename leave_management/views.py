from django.views.generic import CreateView, DetailView, ListView

from .forms import LeaveRequestForm
from .models import LeaveRequest


class LeaveListView(ListView):
    model = LeaveRequest
    template_name = "leave_management/leave_list.html"


class LeaveApplyView(CreateView):
    model = LeaveRequest
    form_class = LeaveRequestForm
    template_name = "leave_management/leave_apply.html"


class LeaveDetailView(DetailView):
    model = LeaveRequest
    template_name = "leave_management/leave_detail.html"
