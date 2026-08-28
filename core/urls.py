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
]