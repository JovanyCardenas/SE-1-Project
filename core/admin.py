from django.contrib import admin
from .models import *

# Register your models here.

@admin.register(FeatureToggle)
class FeatureToggleAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active")
    list_editable = ("is_active",)
    search_fields = ("name", "slug")