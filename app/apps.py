from django.apps import AppConfig
import time


class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self):
        from .utils import startSchedular, GenerateBRCode
        # startSchedular()
        GenerateBRCode().start()
        