from django.apps import AppConfig


class GroceryStoreAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'grocery_store_app'

    def ready(self):
        # Import signal handlers
        from .models import geocode_store