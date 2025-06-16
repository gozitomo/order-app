import logging
from django.contrib.auth.views import LoginView
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils.timezone import now
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import CustomSignupForm
from .models import HeroContent, HomeContent
from users.models import UserProfile, UserGroup
from users.models import UserProfile
from users.models import User

# Create decorators

def admin_required(view_func):
    return user_passes_test(lambda u: u.is_superuser)(view_func)

@login_required
def home_page(request):
    home_contents = HomeContent.objects.all()

    return render(request, 'sitecontent/home.html', {
        'home_contents': home_contents,
    })

# Create your views here.
def signup(request):
    if request.method == 'POST':
        form = CustomSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            address = form.cleaned_data['address']
            UserProfile.objects.create(user=user, address=address)
            login(request, user)
            return redirect('home_page')
    else:
        form = CustomSignupForm()
    return render(request, 'sitecontent/signup.html', {'form': form})


logger = logging.getLogger('django.security.Authentication')

class CustomLoginView(LoginView):
    template_name = 'sitecontent/login.html'

    def form_invalid(self, form):
        username = form.cleaned_data.get('username') or self.request.POST.get('username')
        ip = self.request.META.get('REMOTE_ADDR')

        try:
            user = User.objects.get(username=username)
            if not user.is_active:
                reason = 'account is inactive'
            else:
                reason = 'incorrect password'
        except User.DoesNotExist:
            reason = 'user does not exist'

        logger.warning(f"[LOGIN FAILED] user={username!r} ip={ip} reason={reason}")
        messages.error(self.request, "ログインに失敗しました。ユーザー名またはパスワードをご確認ください。")
        return super().form_invalid(form)