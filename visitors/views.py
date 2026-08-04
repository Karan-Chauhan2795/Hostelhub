from django.views.generic import CreateView, ListView, TemplateView

from .forms import VisitorForm
from .models import Visitor


class VisitorListView(ListView):
    model = Visitor
    template_name = "visitors/visitor_list.html"


class VisitorCreateView(CreateView):
    model = Visitor
    form_class = VisitorForm
    template_name = "visitors/visitor_create.html"


class VisitorHistoryView(TemplateView):
    template_name = "visitors/visitor_history.html"
