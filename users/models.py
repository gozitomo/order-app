from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class UserGroup(models.Model):
    group_id = models.PositiveIntegerField(unique=True, blank=True, null=True)
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    postal_code = models.CharField(max_length=255, default='000-0000')
    address = models.CharField(max_length=255)
    user_group = models.ForeignKey(UserGroup, default=1, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username}のプロフィール"


