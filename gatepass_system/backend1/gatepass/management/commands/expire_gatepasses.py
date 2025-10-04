from django.core.management.base import BaseCommand
from django.utils import timezone
from gatepass.models import Gatepass

class Command(BaseCommand):
    help = 'Expires gatepasses that have not been approved or rejected by parents in time.'

    def handle(self, *args, **options):
        now = timezone.now()
        expired_gatepasses = Gatepass.objects.filter(
            status='PENDING',
            request_expires_at__lte=now
        )

        count = expired_gatepasses.update(status='EXPIRED')

        self.stdout.write(self.style.SUCCESS(f'Successfully expired {count} gatepasses.'))