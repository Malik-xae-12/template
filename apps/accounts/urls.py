from django.urls import path, include

# from app.views.Asset import assetView, checkinView, checkoutView
import apps.accounts.views as authView
from django.contrib.auth import views as auth_views

from django.contrib.sitemaps.views import sitemap


urlpatterns = [
    path('login/', authView.login_user, name='login'),
    path('logout/', authView.logout_user, name='logout'),
    path('register/', authView.register_user, name='register'),
    path('accounts/', include('allauth.urls')),
    path('accounts/password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='Auth/password_reset.html',
             subject_template_name='Auth/password_reset_subject.txt',
             html_email_template_name='Auth/password_reset_email.html'),
         name='password_reset'),
    path('accounts/password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='Auth/password_reset_confirm.html'
         ),
         name='password_reset_confirm'),
    path('accounts/password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='Auth/password_reset_complete.html'
         ),
         name='password_reset_complete'),
    path('accounts/password-reset-done/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='Auth/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('accounts/password-change/',
         authView.ChangePasswordView.as_view(), name='password_change'),
]
