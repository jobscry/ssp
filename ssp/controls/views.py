from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from ssp.utils.views import ActiveTabView

from .models import Control


class ControlListView(ActiveTabView, ListView):
    model = Control
    active_tab = "controls"

    def get_queryset(self):
        return Control.objects.filter(parent=None).all()


class ControlCreateView(ActiveTabView, SuccessMessageMixin, CreateView):
    model = Control
    fields = ("name", "slug", "parent", "body", "is_placeholder")
    success_message = "Control created."
    active_tab = "controls"


class ControlDetailView(ActiveTabView, DetailView):
    model = Control
    active_tab = "controls"


class ControlUpdateView(ActiveTabView, SuccessMessageMixin, UpdateView):
    model = Control
    fields = ("name", "slug", "body", "is_placeholder")
    success_message = "Control updated."
    active_tab = "controls"


class ControlDeleteView(ActiveTabView, DeleteView):
    model = Control
    success_url = reverse_lazy("controls:list")
    active_tab = "controls"
