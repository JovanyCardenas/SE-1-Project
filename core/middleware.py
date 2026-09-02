from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import SystemSetting

User = get_user_model()

class AdminControlsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Handle Impersonation Session
        impersonator_id = request.session.get("_impersonator_id")
        request.is_impersonating = bool(impersonator_id)
        request.original_user = None

        if impersonator_id:
            try:
                request.original_user = User.objects.get(id=impersonator_id)
            except User.DoesNotExist:
                request.session.pop("_impersonator_id", None)
                request.is_impersonating = False

        # 2. Handle Maintenance Mode
        settings_obj = SystemSetting.load()
        if settings_obj.maintenance_mode:
            # Exempt staff, superusers, the original admin if impersonating, and admin login routes
            exempt_paths = [
                reverse("admin:index"),
                reverse("admin:login"),
            ]
            is_staff_or_admin = (
                request.user.is_authenticated and (request.user.is_staff or request.is_impersonating)
            )
            path_exempt = any(request.path.startswith(p) for p in exempt_paths)

            if not is_staff_or_admin and not path_exempt:
                return render(
                    request,
                    "admin/maintenance.html",
                    {"maintenance_message": settings_obj.maintenance_message},
                    status=503,
                )

        return self.get_response(request)