import re

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from ssp.artifacts.models import FileArtifact, artifact_file_name
from ssp.users.tests.factories import UserFactory

DATA_TEXT = b"""Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Urna id volutpat lacus laoreet non curabitur gravida arcu ac. Congue quisque egestas diam in arcu. Egestas tellus rutrum tellus pellentesque eu tincidunt. Morbi blandit cursus risus at ultrices mi. Neque aliquam vestibulum morbi blandit cursus risus. Diam maecenas sed enim ut sem. Integer vitae justo eget magna fermentum iaculis eu. Turpis massa tincidunt dui ut ornare lectus sit amet est. Volutpat blandit aliquam etiam erat velit scelerisque."""
RE_FILEARTIFACT_FILENAME = re.compile(r"^artifacts/\d{14}-")

pytestmark = pytest.mark.django_db


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
