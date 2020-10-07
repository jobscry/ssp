from django.contrib.auth.decorators import login_required, permission_required
from django.urls import path

from .views import (
    ControlCreateView,
    ControlDeleteView,
    ControlDetailView,
    ControlListView,
    ControlUpdateView,
)

app_name = "Controls"
urlpatterns = [
    path(
        "create/",
        view=permission_required("controls.add_control")(ControlCreateView.as_view()),
        name="create",
    ),
    path(
        "update/<str:slug>",
        view=permission_required("controls.change_control")(
            ControlUpdateView.as_view()
        ),
        name="update",
    ),
    path(
        "delete/<str:slug>",
        view=permission_required("controls.change_control")(
            ControlDeleteView.as_view()
        ),
        name="delete",
    ),
    path(
        "<str:slug>/", view=login_required(ControlDetailView.as_view()), name="detail"
    ),
    path(
        "",
        view=login_required(ControlListView.as_view()),
        name="list",
    ),
]
