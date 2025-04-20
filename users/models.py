from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    postal_code = models.CharField(max_length=255, default='000-0000')
    address = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.user.username}のプロフィール"
