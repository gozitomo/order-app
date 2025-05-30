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
