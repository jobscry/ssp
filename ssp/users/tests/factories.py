from secrets import token_urlsafe
from typing import Any, Sequence

from django.contrib.auth import get_user_model
from factory import Faker, post_generation
from factory.django import DjangoModelFactory


class UserFactory(DjangoModelFactory):

    username = Faker("user_name")
    email = Faker("email")
    name = Faker("name")

    @post_generation
    def password(self, create: bool, extracted: Sequence[Any], **kwargs):
        password = extracted if extracted else token_urlsafe(16)
        self.set_password(password)

    class Meta:
        model = get_user_model()
        django_get_or_create = ["username"]
