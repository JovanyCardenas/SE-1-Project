from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import FeatureToggle, SystemSetting

DEFAULT_TOGGLES = [
    {
        "name": "Academic Planner & Calendar",
        "slug": "enable_academic_planner",
        "is_active": True,
    },
    {
        "name": "Student Education Plan (CSEP)",
        "slug": "enable_sep",
        "is_active": True,
    },
    {
        "name": "Course Resource Hub",
        "slug": "enable_hub",
        "is_active": True,
    },
    {
        "name": "Syllabus Auto-Parser",
        "slug": "enable_syllabus_parser",
        "is_active": False,
    },
    {
        "name": "Household Demo Module",
        "slug": "households",
        "is_active": False,
    },
]

@receiver(post_migrate)
def initialize_system_defaults(sender, **kwargs):
    # Only run once for the core app
    if sender.name != "core":
        return

    # Ensure SystemSetting singleton exists
    SystemSetting.load()

    # Seed default toggles safely using get_or_create
    for toggle_data in DEFAULT_TOGGLES:
        FeatureToggle.objects.get_or_create(
            slug=toggle_data["slug"],
            defaults={
                "name": toggle_data["name"],
                "is_active": toggle_data["is_active"],
            },
        )