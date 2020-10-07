from django.db import models
from django.urls import reverse
from mptt.models import MPTTModel, TreeForeignKey


class Control(MPTTModel):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    parent = TreeForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children"
    )

    body = models.TextField()
    is_placeholder = models.BooleanField(default=False)

    def __str__(self):
        return self.slug + " " + self.name

    def get_absolute_url(self):
        return reverse("controls:detail", args=[self.slug])
