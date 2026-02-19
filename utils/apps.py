from django.apps import AppConfig


class UtilsConfig(AppConfig):
    name = 'utils'
    
    def ready(self):
        import sys
        if 'migrate' not in sys.argv and 'makemigrations' not in sys.argv:
            import utils.signals
