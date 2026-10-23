from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.


@login_required
def home(request):
    user = request.user
    is_authorized = user.is_superuser
    return render(request, "dashboard/index.html", {"is_authorized": is_authorized, "title": "Dashboard"})
