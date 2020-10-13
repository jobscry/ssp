import pytest
from django.urls import reverse

from ssp.controls.tests.factories import ControlFactory

pytestmark = pytest.mark.django_db


class TestControlViews:
    def test_ControlListView(self, client, user):
        control1 = ControlFactory()
        ControlFactory(parent=control1)

        user.set_password("test")
        user.save()
        client.login(username=user.username, password="test")
        response = client.get(reverse("controls:list"))
        assert response.status_code == 200
        assert len(response.context_data["control_list"]) == 1
