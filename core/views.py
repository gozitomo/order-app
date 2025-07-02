from django.shortcuts import render
from django.contrib.auth.models import AnonymousUser
from django.utils.timezone import now
import logging

from sitecontent.models import ErrLog

def custom_bad_request(request, exception):
    ip = request.META.get('REMOTE_ADDR')
    path = request.path
    user = request.user
    ErrLog.objects.create(
        timestamp=now(),
        level='WARNING',
        module='core.views.custom_page_not_found',
        user = user,
        message=f"404 Not Found: {path} from IP {ip}",
        traceback=""
    )
    return render(request, "400.html", status=400)

def custom_permission_denied(request, exception):
    ip = request.META.get('REMOTE_ADDR')
    path = request.path
    user = request.user
    ErrLog.objects.create(
        timestamp=now(),
        level='WARNING',
        module='core.views.custom_page_not_found',
        user = user,
        message=f"404 Not Found: {path} from IP {ip}",
        traceback=""
    )
    return render(request, "403.html", status=403)

def custom_page_not_found(request, exception):
    #ファビコンの404は無視してそのまま返す
    if request.path == "/favicon.ico":
        return render(request, "404.html", status=404)
    else:
        ip = request.META.get('REMOTE_ADDR')
        path = request.path
        user = request.user
        ErrLog.objects.create(
            timestamp=now(),
            level='WARNING',
            module='core.views.custom_page_not_found',
            user = user,
            message=f"404 Not Found: {path} from IP {ip}",
            traceback=""
        )

        return render(request, "404.html", status=404)

def custom_server_error(request):
    ip = request.META.get('REMOTE_ADDR')
    path = request.path
    user = request.user
    ErrLog.objects.create(
        timestamp=now(),
        level='WARNING',
        module='core.views.custom_page_not_found',
        user = user,
        message=f"404 Not Found: {path} from IP {ip}",
        traceback=""
    )
    return render(request, "500.html", status=500)

logger = logging.getLogger('django.security.Authentication')

def custom_csrf_failure(request, reason=""):
    ip = request.META.get('REMOTE_ADDR')
    user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')
    logger.warning(f"[CSRF FAILURE] ip={ip} reason={reason} UA={user_agent}")

    user = getattr(request, 'user', None)
    if isinstance(user, AnonymousUser) or not getattr(user, 'is_authenticated', False):
        user = None
    ErrLog.objects.create(
        timestamp=now(),
        level='WARNING',
        module='core.views.csrf_failure',
        user=user,
        message=f"CSRF failure: {reason}",
        traceback=f"IP: {ip}\nUA: {user_agent}"
    )

    return render(request, '403.html', status=403)