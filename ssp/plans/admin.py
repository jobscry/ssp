from django.contrib import admin
from .models import Plan, Entry, Detail, Approval


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    pass


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    pass


@admin.register(Detail)
class DetailAdmin(admin.ModelAdmin):
    pass


@admin.register(Approval)
class Approval(admin.ModelAdmin):
    pass
