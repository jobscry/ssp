from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ArtifactsConfig(AppConfig):
    name = "ssp.artifacts"
    verbose_name = _("Artifacts")
