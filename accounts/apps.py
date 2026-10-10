from django.apps import AppConfig
class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    def ready(self):
        from django.contrib.auth.models import User
        from django.db.models.signals import post_save
        from .models import UserProfile
        def ensure_profile(sender, instance, created, **kwargs):
            UserProfile.objects.get_or_create(user=instance, defaults={'role':'staff' if instance.is_staff else 'citizen'})
        post_save.connect(ensure_profile, sender=User, dispatch_uid='metroserve_ensure_profile')
