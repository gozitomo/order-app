from django.db import models

# Create your models here.

class HeroContent(models.Model):
    title = models.CharField(max_length=100, default='プログレスファーム')
    subtitle = models.CharField(max_length=200, default='B2B')
    note = models.CharField(max_length=200, blank=True, help_text='注釈')

    def __str__(self):
        return f"ヒーローセクション({ self.note })" if self.note else "ヒーローセクション"

class HomeContent(models.Model):
    content = models.TextField()
    note = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"トップページの内容"
        
class OrderNote(models.Model):
    content = models.TextField()
    note = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"注文注意書き({ self.note })" if self.note else "注文注意書き"