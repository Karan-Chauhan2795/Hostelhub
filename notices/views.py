from django.views.generic import DetailView, ListView

from .models import Notice


class NoticeListView(ListView):
    model = Notice
    template_name = "notices/notice_list.html"


class NoticeDetailView(DetailView):
    model = Notice
    template_name = "notices/notice_detail.html"
