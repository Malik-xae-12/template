from django.shortcuts import render

# Create your views here.


from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
import logging
from django.contrib.auth.decorators import user_passes_test

from apps.accounts.group_auth import is_manager
from django.contrib.auth.models import User


# Create a logger object to log necessary information
logger = logging.getLogger(__name__)

# User Login View


class ChangePasswordView(SuccessMessageMixin, PasswordChangeView):
    template_name = 'auth/change_password.html'
    success_message = "Successfully Changed Your Password"
    success_url = reverse_lazy('home')


def login_user(request):
    if request.method == 'POST':
        # Use build-in authenticate function to authenticate user
        remember_me = request.POST.get('rememberme')=='on'
        username = request.POST.get('username')
        user_cookie = ""
        user = authenticate(request, username=request.POST.get(
            'username'), password=request.POST.get('password'))
        if user is not None:
            login(request, user)
            if not remember_me:
                request.session.set_expiry(3600)
            else:
                user_cookie = username
            messages.success(request, f'Welcome {user.get_username()}')
            resp = redirect('home')
            resp.set_cookie('user', user_cookie)
            return resp
        else:
            logger.info("Someone tried to login with invalid credentials")
            messages.warning(request, 'Invalid Credentials!')
            return redirect('home')
    if request.user.is_authenticated:
        return redirect('home')
    user_cookie  = request.COOKIES.get('user', "")
    return render(request, 'auth/login.html', {'title': 'Login', 'user': user_cookie})

def register_user(request):
    if request.method == 'POST':
        uname = request.POST['uname']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 == password2:
            if User.objects.filter(email=email).exists():
                messages.error(request, 'email is already taken by others')
                return redirect('register')
            elif User.objects.filter(username=uname):
                messages.error(request, 'Username is taken by others')
                return redirect('register')
            else:
                user = User.objects.create_user(
                    username=uname, email=email, password=password1)
                messages.success(request, 'Registration Success!')
                return redirect('login')
        else:
            messages.error(request, 'Passwords does not match :(')
            return redirect('register')
    elif request.user.is_authenticated:
        return redirect('home')
    else:
        return render(request, 'auth/register.html', {'title': 'Register'})


@login_required
def logout_user(request):
    logger.info(f"User {request.user} Logged out Successfully!")
    messages.success(request, "Successfully Logged out :)")
    logout(request)
    return redirect('login')

@user_passes_test(is_manager)
def my_view(request):
    pass 