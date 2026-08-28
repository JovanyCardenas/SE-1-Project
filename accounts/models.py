from django.db import models
from django.conf import settings

class Profile(models.Model):
    YEAR_CHOICES = [
        ("freshman", "Freshman"),
        ("sophomore", "Sophomore"),
        ("junior", "Junior"),
        ("senior", "Senior"),
        ("graduate", "Graduate"),
        ("other", "Other"),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    display_name = models.CharField(max_length=100, blank=True)
    school_email = models.EmailField(blank=True)
    major = models.CharField(max_length=100, blank=True)
    year = models.CharField(max_length=20, choices=YEAR_CHOICES, blank=True)
    graduation_year = models.PositiveIntegerField(blank=True, null=True)
    bio = models.TextField(blank=True)
    discord_username = models.CharField(max_length=100, blank=True)
    linkedin_url = models.URLField(blank=True)
    public_profile = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return self.display_name or self.user.username