
from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
# from .models import Users

# class UserAdmin(BaseUserAdmin):
#     list_display = ('email', 'first_name', 'last_name', 'is_active', 'phone_number', 'is_mla')
#     list_filter = ('is_superuser', 'is_active', 'is_mla')
#     fieldsets = (
#         (None, {'fields': ('email', 'password')}),
#         ('Personal info', {'fields': ('first_name', 'last_name',  'phone_number', 'is_mla')}),
#         ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
#         ('Important dates', {'fields': ('last_login', 'date_joined')}),
#     )
#     add_fieldsets = (
#         (None, {
#             'classes': ('wide',),
#             'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'phone_number', 'is_mla'),
#         }),
#     )
#     search_fields = ('email', 'first_name', 'last_name', 'phone_number')
#     ordering = ('email',)

# admin.site.register(Users, UserAdmin)
