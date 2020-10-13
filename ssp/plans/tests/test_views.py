import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied
from django.http.response import Http404
from django.test import RequestFactory
from django.urls import reverse

from ssp.controls.tests.factories import ControlFactory
from ssp.plans.models import Approval, Detail, Entry, Plan
from ssp.plans.tests.factories import DetailFactory, EntryFactory, PlanFactory
from ssp.plans.views import (
    PlanCreateView,
    PlanDetailView,
    plan_control_entry,
)
from ssp.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def request_factory():
    return RequestFactory()


@pytest.fixture
def user():
    p = Permission.objects.get(name="Can change plan")
    u = UserFactory()
    u.user_permissions.add(p)
    u.set_password("test")
    u.save()
    return u


class TestPlanViews:
    def test_BasePlanRestrictedView(self, request_factory, user):
        request = request_factory.get(reverse("plans:create"))
        u = UserFactory()
        request.user = u

        with pytest.raises(PermissionDenied):
            PlanCreateView.as_view()(request)

        request = request_factory.get(reverse("plans:create"))
        request.user = user
        try:
            PlanCreateView.as_view()(request)
        except PermissionDenied:
            pytest.fail("Should not fail")

    def test_PlanCreateView_add_user(self, request_factory, user):
        request = request_factory.post(
            reverse("plans:create"),
            {
                "title": "test",
                "description": "test",
                "root_control": ControlFactory().pk,
            },
        )
        request.user = user
        PlanCreateView.as_view()(request)

        p = Plan.objects.get(title="test")
        assert p.creator.pk == request.user.pk

    def test_PlanDetailView_no_control_slug(self, request_factory, user):
        p = PlanFactory(creator=user)
        request = request_factory.get(p.get_absolute_url())
        request.user = user

        response = PlanDetailView.as_view()(request, pk=p.pk)

        assert "control_list" in response.context_data
        assert "pending_approval" in response.context_data
        assert "pending_approval_count" in response.context_data
        assert "collaborating" in response.context_data
        assert "observing" in response.context_data
        assert "approved" in response.context_data

    def test_PlanDetailView_control_slug(self, request_factory, user):
        p = PlanFactory(creator=user)
        c = ControlFactory()
        request = request_factory.get(
            reverse("plans:plan-control-detail", args=[p.pk, c.slug])
        )
        request.user = user

        response = PlanDetailView.as_view()(request, pk=p.pk, control_slug=c.slug)

        assert "control" in response.context_data
        assert "control_list" in response.context_data

    def test_plan_control_entry(self, request_factory, user):
        p = PlanFactory(creator=user)

        request = request_factory.get(
            reverse("plans:plan-control-entry", args=[9999, "fake-slug"])
        )
        request.user = user

        with pytest.raises(Http404):
            plan_control_entry(request, plan_pk=9999, control_slug="fake-slug")

        with pytest.raises(Http404):
            plan_control_entry(request, plan_pk=p.pk, control_slug="fake-slug")

    def test_plan_control_entry_create_entry(self, request_factory, user):
        p = PlanFactory(creator=user)
        c = ControlFactory()

        request = request_factory.get(
            reverse("plans:plan-control-entry", args=[9999, "fake-slug"])
        )
        request.user = user

        assert Entry.objects.filter(plan=p).count() == 0
        plan_control_entry(request, plan_pk=p.pk, control_slug=c.slug)
        assert Entry.objects.filter(plan=p).count() == 1

        p = PlanFactory(creator=user)
        EntryFactory(plan=p, control=c)
        assert Entry.objects.filter(plan=p).count() == 1
        plan_control_entry(request, plan_pk=p.pk, control_slug=c.slug)
        assert Entry.objects.filter(plan=p).count() == 1

    def test_plan_control_entry_draft_detail(self, client, user):
        p = PlanFactory(creator=user)
        c = ControlFactory()
        e = EntryFactory(plan=p, control=c)
        d = DetailFactory(entry=e, status=Detail.DRAFT)

        client.login(username=user.username, password="test")
        response = client.get(reverse("plans:plan-control-entry", args=[p.pk, c.slug]))
        assert response.status_code == 200
        assert response.context["detail"].pk == d.pk

    def test_plan_control_entry_pending_approval_detail(self, client, user):
        p = PlanFactory(creator=user)
        c = ControlFactory()
        e = EntryFactory(plan=p, control=c)
        d = DetailFactory(entry=e, status=Detail.PENDING_APPROVAL)

        e.approvers.add(user)
        e.collaborators.add(user)

        client.login(username=user.username, password="test")
        response = client.get(reverse("plans:plan-control-entry", args=[p.pk, c.slug]))
        assert response.status_code == 200
        assert response.context["detail"].pk == d.pk

        assert response.context["can_approve"] is True
        assert response.context["can_collaborate"] is True
        assert response.context["approval"] is None

        a = Approval.objects.create(detail=d, user=user, plan=p)
        response = client.get(reverse("plans:plan-control-entry", args=[p.pk, c.slug]))
        assert response.status_code == 200
        assert response.context["approval"].pk == a.pk

    def test_plan_control_entry_published_detail(self, client, user):
        p = PlanFactory(creator=user)
        c = ControlFactory()
        e = EntryFactory(plan=p, control=c)
        d = DetailFactory(entry=e, status=Detail.PUBLISHED)

        e.approvers.add(user)
        e.collaborators.add(user)

        client.login(username=user.username, password="test")
        response = client.get(reverse("plans:plan-control-entry", args=[p.pk, c.slug]))
        assert response.status_code == 200
        assert response.context["detail"].pk == d.pk

        assert response.context["can_approve"] is False
        assert response.context["can_collaborate"] is False
        assert response.context["approval"] is None

    def test_create_detail(self, client, user):
        client.login(username=user.username, password="test")
        response = client.get(reverse("plans:create-detail", args=[99999]))

        assert response.status_code == 404

        p = PlanFactory(creator=user)
        c = ControlFactory()
        e = EntryFactory(plan=p, control=c)

        assert Detail.objects.filter(entry=e).count() == 1
        response = client.get(reverse("plans:create-detail", args=[e.pk]))
        assert Detail.objects.filter(entry=e).count() == 2

    def test_create_detail_draft_or_pa_exists(self, client, user):
        p = PlanFactory(creator=user)
        c = ControlFactory()
        e = EntryFactory(plan=p, control=c)
        DetailFactory(entry=e, status=Detail.DRAFT)

        client.login(username=user.username, password="test")
        response = client.get(reverse("plans:create-detail", args=[e.pk]))

        assert response.status_code == 403

    def test_toggle_approval(self, client, user):
        client.login(username=user.username, password="test")
        response = client.get(reverse("plans:toggle-approve-detail", args=[99999]))

        assert response.status_code == 404

    def test_toggle_approval_check_permissions(self, client, user):
        p = PlanFactory(creator=user)
        c = ControlFactory()
        e = EntryFactory(plan=p, control=c)
        d = DetailFactory(entry=e, status=Detail.PENDING_APPROVAL)

        user2 = UserFactory()
        user2.set_password("test")
        user2.save()
        client.login(username=user2.username, password="test")
        response = client.get(reverse("plans:toggle-approve-detail", args=[d.pk]))
        assert response.status_code == 403

        e.approvers.add(user2)
        response = client.get(reverse("plans:toggle-approve-detail", args=[d.pk]))
        assert response.status_code != 403

    def test_toggle_approval_approve_unapprove(self, client, user):
        p = PlanFactory(creator=user)
        c = ControlFactory()
        e = EntryFactory(plan=p, control=c)
        d = DetailFactory(entry=e, status=Detail.PENDING_APPROVAL)

        client.login(username=user.username, password="test")
        assert Approval.objects.filter(detail=d, user=user).count() == 0
        client.get(reverse("plans:toggle-approve-detail", args=[d.pk]))
        assert Approval.objects.filter(detail=d, user=user).count() == 1

        client.get(reverse("plans:toggle-approve-detail", args=[d.pk]))
        assert Approval.objects.filter(detail=d, user=user).count() == 0


class TestDetailView:
    def test_DetailUpdateView_permissions(self, client, user):
        e = EntryFactory()
        d = DetailFactory(entry=e, status=Detail.DRAFT)

        u = UserFactory()
        u.set_password("test")
        u.save()
        client.login(username=u.username, password="test")
        response = client.get(reverse("plans:update-detail", args=[d.pk]))
        assert response.status_code == 403

        e.collaborators.add(user)
        client.login(username=user.username, password="test")
        response = client.get(reverse("plans:update-detail", args=[d.pk]))
        assert response.status_code == 200
