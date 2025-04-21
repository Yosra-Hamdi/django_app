# core/utils.py
from django.contrib.auth import get_user_model
from .middleware import _active

class set_current_user:
    """Context manager pour définir un utilisateur temporaire"""
    
    def __init__(self, user):
        self.user = user
    
    def __enter__(self):
        self.prev_request = getattr(_active, 'request', None)
        _active.request = type('Request', (), {'user': self.user})()
    
    def __exit__(self, *args):
        _active.request = self.prev_request