from kuser.views import MyAdminSite
from django.contrib.auth.models import Group, User
from rest_framework.authtoken.models import Token
from fcm_django.models import FCMDevice
from rest_framework.authtoken.admin import TokenAdmin

my_admin_site = MyAdminSite(name='myadmin')

my_admin_site.register(Group)
my_admin_site.register(User)
my_admin_site.register(FCMDevice)
my_admin_site.register(Token, TokenAdmin)

def my_admin_register(model):
    def decorator(admin_class):
        my_admin_site.register(model, admin_class)
        return admin_class
    return decorator