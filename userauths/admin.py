from django.contrib import admin
from userauths.models import User, Profile

# Register your models here.
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'full_name', 'email', 'gender', 'phone']

class ProfileAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'user', 'verified']
    list_editable = ['verified']


admin.site.register(User, UserAdmin) #register user model to admin section
admin.site.register(Profile, ProfileAdmin)

