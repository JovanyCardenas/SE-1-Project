from django.urls import path
from .views import *

urlpatterns = [
    path("", home, name="home"),
    path("coming-soon/", coming_soon, name="coming_soon"),
    path("dashboard/", dashboard, name="dashboard"),
    path("about/", about, name="about"),
    path("contact/", contact, name="contact"),
    path("resources/", resources, name="resources"),
    path("settings/", settings, name="settings"),
    path("feature-toggles/", feature_toggle, name="feature_toggle"),
    path("staff/admin-tools/", admin_tools, name="admin_tools"),
    path("staff/impersonate/<int:user_id>/", impersonate_user, name="impersonate_user"),
    path("staff/stop-impersonation/", stop_impersonation, name="stop_impersonation"),
]