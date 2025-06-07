from django.contrib import admin
from .models import HeroContent, HomeContent, OrderNote, OrderHistoryNote, ErrLog, ErrMsg, MailTemplate

# Register your models here.

admin.site.register(HeroContent)
admin.site.register(HomeContent)
admin.site.register(OrderNote)
admin.site.register(OrderHistoryNote)

@admin.register(MailTemplate)
class MailTemplateAdmin(admin.ModelAdmin):
    list_display=('key', 'subject')
    search_field=('key', 'subject')

@admin.register(ErrLog)
class ErrLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'level', 'module', 'message', 'user', 'resolved')
    list_filter = ('level', 'resolved')
    search_field = ('message', 'module')

@admin.register(ErrMsg)
class ErrMsgAdmin(admin.ModelAdmin):
    list_display = ('key', 'message', 'is_active')
    search_field = ('key', 'message')

