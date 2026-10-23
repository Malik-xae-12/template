from django.apps import AppConfig


class MedfilesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.medfiles'

    def ready(self):
        import apps.medfiles.signals 
