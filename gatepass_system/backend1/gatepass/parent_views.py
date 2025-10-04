from django.views import View
from django.views.generic import ListView
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.http import JsonResponse
from django.urls import reverse
from .models import ApprovalToken, Gatepass, Parent
from django.core.exceptions import PermissionDenied

class ParentDashboardView(LoginRequiredMixin, ListView):
    model = Gatepass
    template_name = 'gatepass/parent_dashboard.html'
    context_object_name = 'gatepasses'
    paginate_by = 10

    def get_queryset(self):
        try:
            parent = Parent.objects.get(profile=self.request.user.profile)
            return Gatepass.objects.filter(
                student__in=parent.students.all()
            ).order_by('-created_at')
        except Parent.DoesNotExist:
            return Gatepass.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            parent = Parent.objects.get(profile=self.request.user.profile)
            context['pending_requests'] = Gatepass.objects.filter(
                student__in=parent.students.all(),
                status='PENDING_PARENT'
            ).order_by('request_expires_at')
            context['children'] = parent.students.all()
        except Parent.DoesNotExist:
            context['pending_requests'] = []
            context['children'] = []
        return context

class ParentApprovalView(LoginRequiredMixin, View):
    def post(self, request, gatepass_id):
        try:
            parent = Parent.objects.get(profile=request.user.profile)
            gatepass = get_object_or_404(Gatepass, id=gatepass_id)
            
            # Verify this parent has authority over this student
            if gatepass.student not in parent.students.all():
                raise PermissionDenied("You don't have permission to approve this request")
            
            action = request.POST.get('action')
            if action not in ['approve', 'reject']:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid action'
                }, status=400)

            if gatepass.status != 'PENDING_PARENT':
                return JsonResponse({
                    'success': False,
                    'message': 'This request is no longer pending parent approval'
                }, status=400)

            if action == 'approve':
                gatepass.status = 'PENDING_WARDEN'
                message = 'Request approved and sent to warden'
            else:
                gatepass.status = 'REJECTED'
                message = 'Request rejected'

            gatepass.save()
            
            return JsonResponse({
                'success': True,
                'message': message,
                'new_status': gatepass.status,
                'status_color': gatepass.get_status_color()
            })

        except Parent.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Parent profile not found'
            }, status=403)
        except PermissionDenied as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=403)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)