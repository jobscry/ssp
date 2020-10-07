from django.urls import path

from .views import (
    PlanCreateView,
    PlanDeleteView,
    PlanDetailView,
    PlanListView,
    PlanUpdateView,
    plan_control_entry,
    create_detail,
    DetailUpdateView,
    DetailDeleteView,
    EntryUpdateView,
    toggle_detail_approval,
)

app_name = "Plans"
urlpatterns = [
    path("create/", view=PlanCreateView.as_view(), name="create",),
    path("update/<int:pk>", view=PlanUpdateView.as_view(), name="update",),
    path("delete/<int:pk>", view=PlanDeleteView.as_view(), name="delete",),
    path("entry/<int:entry_pk>/create/", view=create_detail, name="create-detail",),
    path(
        "entry/<int:pk>/people/", view=EntryUpdateView.as_view(), name="update-entry",
    ),
    path(
        "detail/<int:pk>/edit/", view=DetailUpdateView.as_view(), name="update-detail",
    ),
    path(
        "detail/<int:pk>/delete/",
        view=DetailDeleteView.as_view(),
        name="delete-detail",
    ),
    path(
        "detail/<int:pk>/approve/",
        view=toggle_detail_approval,
        name="toggle-approve-detail",
    ),
    path("<int:pk>/", view=PlanDetailView.as_view(), name="detail"),
    path(
        "<int:plan_pk>/<slug:control_slug>/detail/",
        view=plan_control_entry,
        name="plan-control-entry",
    ),
    path(
        "<int:pk>/<slug:control_slug>/",
        view=PlanDetailView.as_view(),
        name="plan-control-detail",
    ),
    path("", view=PlanListView.as_view(), name="list",),
]
