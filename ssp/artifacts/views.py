from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView
from django.views.generic.list import ListView

from ssp.utils.views import ActiveTabView

from .models import FileArtifact


class BaseArtifactView(LoginRequiredMixin, ActiveTabView):
    active_tab = "artifacts"


class FileArtifactListView(BaseArtifactView, ListView):
    model = FileArtifact
    queryset = FileArtifact.objects.select_related()


class FileArtifactDetailView(BaseArtifactView, DetailView):
    model = FileArtifact


class FileArtifactCreateView(BaseArtifactView, PermissionRequiredMixin, CreateView):
    model = FileArtifact
    fields = ("name", "upload")
    permission_required = "artifacts.add_fileartifact"

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.creator = self.request.user
        self.object.save()
        return redirect("artifacts:list")


class FileArtifactDeleteView(BaseArtifactView, DeleteView):
    model = FileArtifact
    success_url = reverse_lazy("artifacts:list")

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=None)
        if not self.request.user.has_perms("artifacts.delete_artifact"):
            if not obj.creator.pk == self.request.user.pk:
                raise PermissionDenied
        return obj
