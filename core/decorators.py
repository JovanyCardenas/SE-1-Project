from functools import wraps
from django.http import Http404
from .models import FeatureToggle

def feature_required(flag_key):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            is_enabled = FeatureToggle.objects.filter(slug=flag_key, is_active=True).exists()
            if not is_enabled:
                raise Http404("Feature not enabled")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator