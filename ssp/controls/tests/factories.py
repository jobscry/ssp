from factory.django import DjangoModelFactory
from factory import Sequence


from ssp.controls.models import Control


class ControlFactory(DjangoModelFactory):
    name = Sequence(lambda n: "control %03d" % n)
    slug = Sequence(lambda n: "control-slug-%03d" % n)
    body = Sequence(lambda n: "control body %03d" % n)

    class Meta:
        model = Control
