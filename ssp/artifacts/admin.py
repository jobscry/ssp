from django.contrib import admin
from .models import FileArtifact


@admin.register(FileArtifact)
class FileArtifactAdmin(admin.ModelAdmin):
    pass
