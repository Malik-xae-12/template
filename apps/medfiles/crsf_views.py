from django.conf import settings
from django.shortcuts import redirect

def csrf_failure(request, reason=""):
    # Always redirect user to LOGIN_URL with a flag
    return redirect(f"{settings.LOGIN_URL}?session_expired=1")
