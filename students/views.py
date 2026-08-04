from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import StudentForm
from .models import Student


class StudentListView(ListView):
    model = Student
    template_name = "students/student_list.html"


class StudentDetailView(DetailView):
    model = Student
    template_name = "students/student_detail.html"


class StudentCreateView(CreateView):
    model = Student
    form_class = StudentForm
    template_name = "students/student_create.html"


class StudentUpdateView(UpdateView):
    model = Student
    form_class = StudentForm
    template_name = "students/student_update.html"


class StudentDeleteView(DeleteView):
    model = Student
    template_name = "students/student_delete.html"
