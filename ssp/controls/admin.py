from django.contrib import admin
from mptt.admin import MPTTModelAdmin

from .models import Control


@admin.register(Control)
class ControlAdmin(MPTTModelAdmin):
    pass
