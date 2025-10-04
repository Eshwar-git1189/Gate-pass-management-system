from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import TemplateView
from django.utils import timezone
from .models import Gatepass

class WardenDashboardView(UserPassesTestMixin, TemplateView):
    template_name = 'warden_dashboard.html'

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get counts for different statuses
        context['pending_count'] = Gatepass.objects.filter(status='PENDING').count()
        context['approved_count'] = Gatepass.objects.filter(status='APPROVED').count()
        context['rejected_count'] = Gatepass.objects.filter(status='REJECTED').count()
        context['active_count'] = Gatepass.objects.filter(
            status='APPROVED',
            exit_time__isnull=False,
            return_time__isnull=True
        ).count()

        # Get recent gatepasses
        context['gatepasses'] = Gatepass.objects.select_related(
            'student', 'student__user'
        ).order_by('-created_at')[:50]

        return context

class SecurityDashboardView(UserPassesTestMixin, TemplateView):
    template_name = 'security_dashboard.html'

    def test_func(self):
        return hasattr(self.request.user, 'security')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()

        # Students currently out
        context['students_out'] = Gatepass.objects.filter(
            status='APPROVED',
            exit_time__isnull=False,
            return_time__isnull=True
        ).count()

        # Expected returns today
        context['expected_returns'] = Gatepass.objects.filter(
            status='APPROVED',
            exit_time__isnull=False,
            return_time__isnull=True,
            expected_return__date=now.date()
        ).count()

        # Pending verifications (approved but not yet exited)
        context['pending_verifications'] = Gatepass.objects.filter(
            status='APPROVED',
            exit_time__isnull=True
        ).count()

        # Active gatepasses
        context['active_gatepasses'] = Gatepass.objects.filter(
            status='APPROVED',
            exit_time__isnull=False,
            return_time__isnull=True
        ).select_related('student', 'student__user').order_by('expected_return')[:50]

        return context