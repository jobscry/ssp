from django.urls import path

from .views import (
    FileArtifactListView,
    FileArtifactDetailView,
    FileArtifactCreateView,
    FileArtifactDeleteView,
)

app_name = "Artifacts"
urlpatterns = [
    path("<int:pk>/", view=FileArtifactDetailView.as_view(), name="detail"),
    path(
        "create/file/",
        view=FileArtifactCreateView.as_view(),
        name="create-file-artifact",
    ),
    path(
        "delete/file/<int:pk>/",
        view=FileArtifactDeleteView.as_view(),
        name="delete-file-artifact",
    ),
    path("", view=FileArtifactListView.as_view(), name="list",),
]
