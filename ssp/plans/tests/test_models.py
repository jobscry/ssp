import pytest
from django.core.exceptions import ValidationError

from ssp.controls.tests.factories import ControlFactory
from ssp.plans.models import Approval, Detail, Entry
from ssp.plans.tests.factories import DetailFactory, EntryFactory, PlanFactory
from ssp.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestPlanModel:
    def test__str__(self):
        p = PlanFactory.build()
        assert p.title == f"{p}"


class TestEntryModel:
    def test_signal_create_initial_detail_for_entry(self):
        p = PlanFactory()
        p.save()
        c = ControlFactory()
        c.save()
        e = Entry.objects.create(plan=p, control=c)

        assert Detail.objects.filter(entry=e).count() == 1

    def test_latest_plublished_detail(self):
        p = PlanFactory()
        p.save()
        c = ControlFactory()
        c.save()
        e = Entry.objects.create(plan=p, control=c)
        d = Detail.objects.get(entry=e)

        assert e.latest_published_detail().pk == d.pk

    def test_clean(self):
        c = ControlFactory()
        c.is_placeholder = True
        c.save()

        p = PlanFactory()

        with pytest.raises(ValidationError):
            e = Entry(plan=p, control=c)
            e.clean()

    def test_user_can_approve(self):
        e = EntryFactory()
        u = UserFactory()

        assert e.user_can_approve(u) is False

        e.approvers.add(u)
        assert e.user_can_approve(u) is True

    def test_user_can_collaborate(self):
        e = EntryFactory()
        u = UserFactory()

        assert e.user_can_collaborate(u) is False

        e.collaborators.add(u)
        assert e.user_can_collaborate(u) is True


class TestDetailModel:
    def test_has_all_approvals(self):
        e = EntryFactory()
        u = UserFactory()

        d = DetailFactory(entry=e, status=Detail.PENDING_APPROVAL)

        assert d.has_all_approvals() is True

        e.approvers.add(u)
        assert d.has_all_approvals() is False

        Approval.objects.create(user=u, detail=d, plan=e.plan)
        assert d.has_all_approvals() is True

    def test_clean_new_multiple_drafts(self):
        e = EntryFactory()
        DetailFactory(entry=e, status=Detail.DRAFT)

        with pytest.raises(ValidationError):
            d = Detail(entry=e, status=Detail.DRAFT)
            d.clean()

    def test_clean_new_multiple_pending_approval(self):
        e = EntryFactory()
        DetailFactory(entry=e, status=Detail.PENDING_APPROVAL)

        with pytest.raises(ValidationError):
            d = Detail(entry=e, status=Detail.PENDING_APPROVAL)
            d.clean()

    def test_clean_existing_modified_published(self):
        d = DetailFactory(status=Detail.PUBLISHED)

        with pytest.raises(ValidationError):
            d.status = Detail.DRAFT
            d.clean()

    def test_clean_existing_publish_missing_approvals(self):
        e = EntryFactory()
        d = DetailFactory(entry=e, status=Detail.PENDING_APPROVAL)
        u = UserFactory()
        e.approvers.add(u)

        with pytest.raises(ValidationError):
            d.status = Detail.PUBLISHED
            d.clean()

        Approval.objects.create(user=u, detail=d, plan=e.plan)

        try:
            d.status = Detail.PUBLISHED
            d.clean()
        except ValidationError:
            pytest.fail("Should not fail")
