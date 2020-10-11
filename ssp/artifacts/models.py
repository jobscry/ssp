import hashlib
import mimetypes
import os
from datetime import datetime, timezone

from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from ssp.utils.models import get_sentinel_user


def artifact_file_name(instance, filename):
    date = datetime.now(timezone.utc)
    return "artifacts/" + date.strftime("%Y%m%d%H%M%S") + "-" + filename


class FileArtifact(models.Model):
    name = models.CharField(max_length=255)
    upload = models.FileField(upload_to=artifact_file_name)
    size = models.PositiveIntegerField(blank=True, null=True)
    file_hash = models.SlugField(max_length=64, blank=True, null=True)
    mime_type = models.CharField(max_length=100, default="unkown")
    file_extension = models.CharField(max_length=25, default="unknown")
    file_encoding = models.CharField(max_length=100, default="unknown")
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET(get_sentinel_user),
    )
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


@receiver(post_save, sender=FileArtifact)
def populate_file_meta_data(sender, instance, created, **kwargs):
    if created:
        instance.size = instance.upload.size

        m = hashlib.sha256()
        with instance.upload.open("rb"):
            for chunk in instance.upload.chunks():
                m.update(chunk)
        instance.file_hash = m.hexdigest()

        file_path = os.path.join(settings.MEDIA_ROOT, instance.upload.name)
        mime_type, file_encoding = mimetypes.guess_type(file_path)
        if mime_type is not None:
            instance.mime_type = mime_type
        if file_encoding is not None:
            instance.file_encoding = file_encoding
        if (file_extension := mimetypes.guess_extension(mime_type)) is not None:
            instance.file_extension = file_extension[1:]

        instance.save()
