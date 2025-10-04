# backend/gatepass/management/commands/expire_gatepasses.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from gatepass.models import Gatepass

class Command(BaseCommand):
    help = "Expire pending gatepasses whose request_expires_at has passed"

    def handle(self, *args, **options):
        now = timezone.now()
        expired = Gatepass.objects.filter(
            status__in=["PENDING_PARENT", "PENDING_WARDEN"],
            request_expires_at__lte=now
        )
        count = 0
        for gp in expired:
            gp.status = "EXPIRED"
            gp.audit.append({"ts": now.isoformat(), "actor":"system","action":"EXPIRED","note":""})
            gp.save()
            count += 1
        self.stdout.write(self.style.SUCCESS(f"Expired {count} gatepasses."))
