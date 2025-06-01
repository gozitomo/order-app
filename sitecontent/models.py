from django.db import models
from django.utils.timezone import now


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
        return f"注文ページの内容"
        
class OrderHistoryNote(models.Model):
    content = models.TextField()
    note = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"注文履歴ページの内容"

class ErrMsg(models.Model):
    key = models.CharField(max_length=100, unique=True, help_text="テンプレート側で使うキー")
    message = models.TextField(help_text="表示するメッセージ本文（html可）")
    is_active = models.BooleanField(default=True, help_text="有効フラグ")

    def __str__(self):
        return f"{self.key}-{self.message[:50]}"

class ErrLog(models.Model):
    timestamp = models.DateTimeField(default=now)
    level = models.CharField(max_length=50, choices=[
        ('INFO', 'info'),
        ('WARNING', 'warning'),
        ('ERROR', 'error'),
        ('CRITICAL', 'critical'),
    ])
    module = models.CharField(max_length=255, blank=True, help_text="エラーが発生した機能や画面名")
    user = models.ForeignKey('auth.User', null=True, blank=True, on_delete=models.SET_NULL)
    message = models.TextField()
    traceback = models.TextField(blank=True, help_text="詳細なトレース（あれば）")
    resolved = models.BooleanField(default=False, help_text="解決済みフラグ")

    def __str__(self):
        return f"[{self.timestamp}] {self.level} -{self.message[:50]}"
