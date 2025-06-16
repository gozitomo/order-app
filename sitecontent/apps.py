from django.apps import AppConfig


class SitecontentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sitecontent'

    def ready(self):
        import sitecontent.signals  # ← signals.py に定義を移す場合はこちら
