from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
import logging

@receiver(user_logged_in)
def log_login_success(sender, request, user, **kwargs):
    ip = request.META.get('REMOTE_ADDR')
    logger = logging.getLogger('django.security.Authentication')
    logger.info(f"[LOGIN SUCCESS] user={user.username!r} ip={ip}")