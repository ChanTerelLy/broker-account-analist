import functools

from django.conf import settings


def internal_login_required(func, *args, **kwargs):
    @functools.wraps(func)
    def wraps(request, *args, **kwargs):
        if not request:
            request = args[0].context
        if request.headers['x-api-auth'] == settings.INTERNAL_API_TOKEN:
            return func(args[0], *args, **kwargs)
        return {'success': False, 'error': "Permission denided"}
    return wraps
