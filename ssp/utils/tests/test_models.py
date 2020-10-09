import pytest

from ssp.utils.models import get_sentinel_user

pytestmark = pytest.mark.django_db


def test_get_sentinel_user():
    u = get_sentinel_user()
    assert u.username == "deleted"
