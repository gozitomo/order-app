from django.contrib import admin
from django.contrib.auth.models import User
from .models import UserProfile, UserGroup

# Register your models here.


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    extra = 1

class UserAdmin(admin.ModelAdmin):
    inlines = (UserProfileInline,)

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(UserProfile)

@admin.register(UserGroup)
class UserGroupAdmin(admin.ModelAdmin):
    list_display = ('group_id', 'name')

    def formatted_group_id(self, obj):
        return f"{obj.group_id:04}"
    formatted_group_id.short_description = 'Group ID'
