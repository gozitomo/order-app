from django.shortcuts import render
import logging

def custom_bad_request(request, exception):
    return render(request, "400.html", status=400)

def custom_permission_denied(request, exception):
    return render(request, "403.html", status=403)

def custom_page_not_found(request, exception):
    return render(request, "404.html", status=404)

def custom_server_error(request):
    return render(request, "500.html", status=500)

logger = logging.getLogger('django.security.Authentication')

def custom_csrf_failure(request, reason=""):
    ip = request.META.get('REMOTE_ADDR')
    user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')
    logger.warning(f"[CSRF FAILURE] ip={ip} reason={reason} UA={user_agent}")
    return render(request, '403.html', status=403)