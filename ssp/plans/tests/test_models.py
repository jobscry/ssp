import re

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from ssp.artifacts.models import FileArtifact, artifact_file_name
from ssp.controls.tests.factories import ControlFactory
from ssp.plans.models import Approval, ControlDemotionException, Detail, Entry
from ssp.plans.tests.factories import DetailFactory, EntryFactory, PlanFactory
from ssp.users.tests.factories import UserFactory

DATA_TEXT = b"""Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Urna id volutpat lacus laoreet non curabitur gravida arcu ac. Congue quisque egestas diam in arcu. Egestas tellus rutrum tellus pellentesque eu tincidunt. Morbi blandit cursus risus at ultrices mi. Neque aliquam vestibulum morbi blandit cursus risus. Diam maecenas sed enim ut sem. Integer vitae justo eget magna fermentum iaculis eu. Turpis massa tincidunt dui ut ornare lectus sit amet est. Volutpat blandit aliquam etiam erat velit scelerisque."""
RE_FILEARTIFACT_FILENAME = re.compile(r"^artifacts/\d{14}-")

pytestmark = pytest.mark.django_db


class TestPlanModel:
    def test__str__(self):
        p = PlanFactory.build()
        assert p.title == f"{p}"

    def test_plan_clean(self):
        c1 = ControlFactory()
        c2 = ControlFactory(parent=c1)
        p = PlanFactory(root_control=c2)

        with pytest.raises(ValidationError):
            p.clean()

    def test_stop_control_demotion(self):
        c1 = ControlFactory()
        c2 = ControlFactory()
        p = PlanFactory(root_control=c2)

        assert p.root_control.parent is None

        with pytest.raises(ControlDemotionException):
            c2.parent = c1
            c2.save()

            assert p.root_control.parent is not None


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


def test_artifact_file_name():
    filename = artifact_file_name(None, "test")
    assert RE_FILEARTIFACT_FILENAME.search(filename) is not None
    assert filename.endswith("-test")


class TestFileArtifactModel:
    def test_populate_file_meta_data(self):
        a = FileArtifact.objects.create(
            name="test",
            upload=SimpleUploadedFile("test.txt", DATA_TEXT),
            creator=UserFactory(),
        )
        a.save()
        assert a.size == 571
        assert a.mime_type == "text/plain"
        assert a.file_extension == "txt"
        assert a.file_encoding == "unknown"
        assert (
            a.file_hash
            == "6d214576be99e98ebe5646a1302ba1ad921fb031e3e1c69d96244009dae3a873"
        )
