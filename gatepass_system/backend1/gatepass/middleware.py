from django.utils import timezone
from .models import Gatepass

class GatepassExpiryMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check and expire gatepasses before processing the request
        now = timezone.now()
        Gatepass.objects.filter(
            status='PENDING',
            request_expires_at__lte=now
        ).update(
            status='EXPIRED'
        )
        
        return self.get_response(request)