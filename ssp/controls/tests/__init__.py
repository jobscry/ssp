from factory.django import DjangoModelFactory

from ssp.controls.models import Control


class ControlFactory(DjangoModelFactory):
    class Meta:
        model = Control
        django_get_or_create = ["name", "slug", "parent"]
