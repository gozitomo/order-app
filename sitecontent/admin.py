from django.contrib import admin
from .models import HeroContent, HomeContent, OrderNote, OrderHistoryNote

# Register your models here.

admin.site.register(HeroContent)
admin.site.register(HomeContent)
admin.site.register(OrderNote)
admin.site.register(OrderHistoryNote)
