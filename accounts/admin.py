from django.contrib import admin
from .models import *


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "display_name",
        "major",
        "year",
        "graduation_year",
        "public_profile",
        "created_at",
    )
    list_filter = (
        "year",
        "public_profile",
    )
    search_fields = (
        "user__username",
        "user__email",
        "display_name",
        "major",
        "discord_username",
    )