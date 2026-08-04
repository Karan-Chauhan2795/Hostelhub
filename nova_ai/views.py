from django.views.generic import TemplateView


class NovaAIChatView(TemplateView):
    template_name = "nova_ai/chat.html"
