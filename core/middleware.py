from threading import local

_active = local()

class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        _active.request = request
        response = self.get_response(request)
        _active.request = None
        return response

def get_current_user():
    request = getattr(_active, 'request', None)
    if request and hasattr(request, 'user'):
        return request.user
    return None