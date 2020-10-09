from datetime import datetime, timezone

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse_lazy

from ssp.controls.models import Control
from ssp.utils.models import get_sentinel_user


class Plan(models.Model):
    title = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET(get_sentinel_user),
    )
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse_lazy("plans:detail", args=[self.pk])


class Entry(models.Model):
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    control = models.ForeignKey(Control, on_delete=models.CASCADE)
    collaborators = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="entry_collaborations"
    )
    approvers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="entry_approvals"
    )
    observers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="entry_observations"
    )

    class Meta:
        verbose_name_plural = "entries"
        unique_together = ["plan", "control"]

    def latest_published_detail(self):
        return Detail.objects.filter(entry=self, status=Detail.PUBLISHED).latest()

    def clean(self):
        if self.control.is_placeholder:
            raise ValidationError("Cannot create entry for placeholder controls.")

    def user_can_approve(self, user):
        return self.approvers.filter(pk=user.pk).exists()

    def user_can_collaborate(self, user):
        return self.collaborators.filter(pk=user.pk).exists()


class Detail(models.Model):
    DRAFT = "D"
    PENDING_APPROVAL = "PA"
    PUBLISHED = "P"
    STATUS_CHOICES = [
        (DRAFT, "Draft"),
        (PENDING_APPROVAL, "Pending Approval"),
        (PUBLISHED, "Published"),
    ]
    STATUS_CHOICES_FORM = [
        (DRAFT, "Draft"),
        (PENDING_APPROVAL, "Pending Approval"),
    ]
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE)
    status = models.CharField(max_length=3, choices=STATUS_CHOICES, default=DRAFT)
    text = models.TextField()
    approvals = models.ManyToManyField(settings.AUTH_USER_MODEL, through="Approval")
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)

    last_status = models.CharField(max_length=3, choices=STATUS_CHOICES, default=DRAFT)
    last_text = models.TextField(null=True, blank=True)
    last_modified_on = models.DateTimeField(blank=True, null=True)

    def has_all_approvals(self):
        needed_approval = set(self.entry.approvers.values_list("pk", flat=True))
        existing_approvals = set(
            self.approvals.values_list("approval__user__pk", flat=True)
        )
        return needed_approval == existing_approvals

    def clean(self):
        if self.pk:
            if self.last_status == self.PUBLISHED:
                raise ValidationError({"status": "Cannot be modified once published."})
            if self.last_status != self.status:  # status changed
                if self.status == self.PUBLISHED:  # now published
                    if not self.has_all_approvals():
                        raise ValidationError(
                            {
                                "status": "Cannot be published without all required approvals."
                            }
                        )
        else:
            if (
                self.status == self.DRAFT
                and Detail.objects.filter(entry=self.entry, status=self.DRAFT).exists()
            ):
                raise ValidationError("Cannot have multiple drafts.")
            if (
                self.status == self.PENDING_APPROVAL
                and Detail.objects.filter(
                    entry=self.entry, status=self.PENDING_APPROVAL
                ).exists()
            ):
                raise ValidationError("Cannot have multiple pending approval.")

    def save(self, *args, **kwargs):
        modified = False
        if self.status != self.last_status or self.text != self.last_text:
            self.last_status = self.status
            self.last_text = self.text
            modified = True

        if modified and self.status == self.PENDING_APPROVAL:
            Approval.objects.filter(detail=self).delete()

        if modified:
            self.last_modified_on = datetime.now(timezone.utc)

        super().save(*args, **kwargs)

    class Meta:
        ordering = [
            "-modified_on",
        ]
        get_latest_by = "modified_on"


class Approval(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET(get_sentinel_user),
    )
    detail = models.ForeignKey(Detail, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["user", "detail"]
        ordering = [
            "created_on",
        ]


@receiver(post_save, sender=Entry)
def create_initial_detail_for_entry(sender, instance, created, **kwargs):
    if created:
        Detail.objects.create(
            entry=instance, status=Detail.PUBLISHED, text="entry created"
        )
