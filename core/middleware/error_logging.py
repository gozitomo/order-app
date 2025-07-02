import logging
import traceback
from django.utils.timezone import now
from sitecontent.models import ErrLog
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)

class ErrorLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            #ロガー出力
            logger.error("Unhandled Exception", exc_info=True)

            #DB保存
            user = getattr(request, 'user', None)
            if isinstance(user, AnonymousUser) or not getattr(user, 'is_authenticated', False):
                user = None
            tb = traceback.format_exc()

            ErrLog.objects.create(
                timestamp=now(),
                level='error',
                module='core.middleware',
                user=user,
                message=str(e),
                traceback=tb,
            )
            
            raise
