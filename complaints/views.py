from django.views.generic import CreateView, DetailView, ListView

from .forms import ComplaintForm
from .models import Complaint


class ComplaintListView(ListView):
    model = Complaint
    template_name = "complaints/complaint_list.html"


class ComplaintCreateView(CreateView):
    model = Complaint
    form_class = ComplaintForm
    template_name = "complaints/complaint_create.html"


class ComplaintDetailView(DetailView):
    model = Complaint
    template_name = "complaints/complaint_detail.html"
