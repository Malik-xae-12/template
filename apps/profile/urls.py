from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import ProfileView
urlpatterns = [
    path('', ProfileView.as_view(), name='profile'),
]