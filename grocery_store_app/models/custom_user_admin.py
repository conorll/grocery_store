from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User


class CustomUserAdmin(UserAdmin):    
    actions = None

    # Display all users with relevant details
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined')
    
    # Search functionality
    search_fields = ('username', 'email', 'first_name', 'last_name')
    
    # Filtering options
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    
    # Provide fields to update
    fields = ('username', 'first_name', 'last_name', 'email')
    
    # Remove fieldsets to use the simple fields layout
    fieldsets = None
