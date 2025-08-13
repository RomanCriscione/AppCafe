from django.apps import AppConfig

class ReviewsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "reviews"

    def ready(self):
        # Importa los signals de ESTA app
        import reviews.signals  # noqa: F401
