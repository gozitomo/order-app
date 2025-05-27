from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class UserGroup(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=255, blank=True)
    postal_code = models.CharField(max_length=255, default='000-0000')
    address = models.CharField(max_length=255)
    region = models.ForeignKey(ShippingRegion, related_name='users', on_delete=models.CASCADE)
    user_group = models.ForeignKey(UserGroup, null=True, blank=True, on_delete=models.CASCADE)
    def __str__(self):
        return f"{self.user.username}のプロフィール"


