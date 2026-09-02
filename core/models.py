from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

# Create your models here.

# This model is for admins to be able to toggle what features are active at all times
class FeatureToggle(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="Human-readable name")
    slug = models.SlugField(max_length=50, unique=True, help_text="Identifier used in code/templates")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({'ON' if self.is_active else 'OFF'})"

class SystemSetting(models.Model):
    maintenance_mode = models.BooleanField(default=False)
    maintenance_message = models.TextField(default="We are currently performing scheduled maintenance. Please check back shortly.")

    def save(self, *args, **kwargs):
        # Guarantee singleton pattern
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

class SiteBanner(models.Model):
    BANNER_TYPES = (
        ("info", "Information (Blue)"),
        ("warning", "Warning (Amber)"),
        ("danger", "Alert / Critical (Red)"),
        ("success", "Success (Green)"),
    )
    message = models.CharField(max_length=255)
    banner_type = models.CharField(max_length=10, choices=BANNER_TYPES, default="info")
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.get_banner_type_display()}] {self.message[:40]}"