from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied
from .models import *
from .signals import DEFAULT_TOGGLES
from django.contrib import messages
from django.contrib.auth import login, get_user_model

User = get_user_model()


# ADMINISTRATOR TOOLS
@staff_member_required
def admin_tools(request):
    if not request.user.is_superuser:
        raise PermissionDenied

    system_setting = SystemSetting.load()
    banners = SiteBanner.objects.all().order_by("-created_at")
    recent_users = User.objects.exclude(id=request.user.id).order_by("-date_joined")[:15]

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "seed_default_toggles":
            created_count = 0
            for toggle_data in DEFAULT_TOGGLES:
                _, created = FeatureToggle.objects.get_or_create(
                    slug=toggle_data["slug"],
                    defaults={
                        "name": toggle_data["name"],
                        "is_active": toggle_data["is_active"],
                    },
                )
                if created:
                    created_count += 1
            messages.success(
                request,
                f"Default feature toggles synchronized. ({created_count} newly created)",
            )

        elif action == "update_maintenance":
            system_setting.maintenance_mode = "maintenance_mode" in request.POST
            system_setting.maintenance_message = request.POST.get("maintenance_message", "")
            system_setting.save()
            messages.success(request, "Maintenance settings updated.")

        # ... your existing banner actions ...

        return redirect("admin_tools")

    return render(
        request,
        "admin/admin_tools.html",
        {
            "system_setting": system_setting,
            "banners": banners,
            "recent_users": recent_users,
        },
    )


@staff_member_required
def impersonate_user(request, user_id):
    if not request.user.is_superuser:
        raise PermissionDenied

    target_user = get_object_or_404(User, id=user_id)

    # Store real superuser ID in session before login switch
    current_admin_id = request.session.get("_impersonator_id") or request.user.id
    login(request, target_user)
    request.session["_impersonator_id"] = current_admin_id

    messages.warning(request, f"You are now impersonating {target_user.username}.")
    return redirect("home")


def stop_impersonation(request):
    impersonator_id = request.session.get("_impersonator_id")
    if not impersonator_id:
        return redirect("home")

    admin_user = get_object_or_404(User, id=impersonator_id)
    login(request, admin_user)
    request.session.pop("_impersonator_id", None)

    messages.success(request, "Returned to your superuser account.")
    return redirect("admin_tools")

@staff_member_required
def feature_toggle(request):
    if not request.user.is_superuser:
        raise PermissionDenied

    if request.method == "POST":
        toggle_id = request.POST.get("toggle_id")
        toggle = FeatureToggle.objects.get(id=toggle_id)
        toggle.is_active = not toggle.is_active
        toggle.save()
        return redirect("feature_toggle")

    toggles = FeatureToggle.objects.all()
    return render(request, "admin/feature_toggle.html", {"toggles": toggles})




# NON ADMIN VIEWS
def coming_soon(request):
    return render(request, "coming_soon.html")

def home(request):
    return render(request, "pages/home.html")

def about(request):
    return render(request, "pages/about.html")

def contact(request):
    return render(request, "pages/contact.html")

def resources(request):
    return render(request, "coming_soon.html")
    # return render(request, "pages/resources.html")

@login_required
def settings(request):
    return render(request, "coming_soon.html")
    # return render(request, "pages/settings.html")

@login_required
def dashboard(request):
    return render(request, "pages/dashboard.html")