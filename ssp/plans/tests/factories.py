from factory import Sequence, SubFactory
from factory.django import DjangoModelFactory

from ssp.controls.tests.factories import ControlFactory
from ssp.plans.models import Detail, Entry, Plan
from ssp.users.tests.factories import UserFactory


class PlanFactory(DjangoModelFactory):
    title = Sequence(lambda n: "plan %03d" % n)
    description = Sequence(lambda n: "plan description %03d" % n)
    creator = SubFactory(UserFactory)

    class Meta:
        model = Plan


class EntryFactory(DjangoModelFactory):
    plan = SubFactory(PlanFactory)
    control = SubFactory(ControlFactory)

    class Meta:
        model = Entry


class DetailFactory(DjangoModelFactory):
    entry = SubFactory(EntryFactory)
    text = Sequence(lambda n: "detail text %03d" % n)

    class Meta:
        model = Detail
