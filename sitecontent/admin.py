from django.contrib import admin
from .models import HeroContent, HomeContent, OrderNote, OrderHistoryNote, ErrLog, ErrMsg

# Register your models here.

admin.site.register(HeroContent)
admin.site.register(HomeContent)
admin.site.register(OrderNote)
admin.site.register(OrderHistoryNote)

@admin.register(ErrLog)
class ErrLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'level', 'module', 'message', 'user', 'resolved')
    list_filter = ('level', 'resolved')
    search_field = ('message', 'module')

@admin.register(ErrMsg)
class ErrMsgAdmin(admin.ModelAdmin):
    list_display = ('key', 'message', 'is_active')
    search_field = ('key', 'message')

