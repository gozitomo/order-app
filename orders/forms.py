from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class CustomSignupForm(UserCreationForm):
    address = forms.CharField(label='住所', required=True)

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2', 'address')
