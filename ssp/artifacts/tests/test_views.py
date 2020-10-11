import pytest
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from ssp.artifacts.models import FileArtifact
from ssp.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    p = Permission.objects.get(name="Can add file artifact")
    u = UserFactory()
    u.user_permissions.add(p)
    u.set_password("test")
    u.save()
    return u


class TestFileArtifactViews:
    def test_FileArtifactCreateView_populate_creator(self, client, user):
        text_file = SimpleUploadedFile(
            "test.txt", b"hello world", content_type="text/plain"
        )

        client.login(username=user.username, password="test")
        response = client.post(
            reverse("artifacts:create-file-artifact"),
            {
                "name": "test_FileArtifactCreateView_populate_creator",
                "upload": text_file,
            },
        )
        assert response.status_code == 302
        a = FileArtifact.objects.get(
            name="test_FileArtifactCreateView_populate_creator"
        )
        assert a.creator.pk == user.pk

    def test_FileArtifactDeleteView_permissions(self, client, user):
        a = FileArtifact.objects.create(
            name="test",
            upload=SimpleUploadedFile("test.txt", b"hello world"),
            creator=user,
        )
        a.save()

        user2 = UserFactory()
        user2.set_password("test")
        user2.save()

        client.login(username=user2.username, password="test")
        response = client.get(reverse("artifacts:delete-file-artifact", args=[a.pk]))
        assert response.status_code == 403

        a = FileArtifact.objects.create(
            name="test",
            upload=SimpleUploadedFile("test.txt", b"hello world"),
            creator=user2,
        )
        a.save()

        response = client.get(reverse("artifacts:delete-file-artifact", args=[a.pk]))
        assert response.status_code == 200
