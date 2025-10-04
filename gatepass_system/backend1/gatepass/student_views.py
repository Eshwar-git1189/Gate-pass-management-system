from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, ListView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from .models import Gatepass, Student
from .forms import GatepassRequestForm
from datetime import timedelta

class StudentRequestView(LoginRequiredMixin, CreateView):
    form_class = GatepassRequestForm
    template_name = 'student_request.html'
    success_url = reverse_lazy('student-gatepass-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get recent requests for this student
        context['recent_requests'] = Gatepass.objects.filter(
            student__profile=self.request.user.profile
        ).order_by('-created_at')[:10]
        return context

    def form_valid(self, form):
        try:
            student = Student.objects.get(profile=self.request.user.profile)
        except Student.DoesNotExist:
            messages.error(self.request, "Student profile not found.")
            return self.form_invalid(form)

        # The form's clean method already validates the datetime fields
        gatepass = form.save(commit=False)
        gatepass.student = student
        gatepass.status = 'PENDING_PARENT'
        
        try:
            gatepass.save()
            # Send email notifications
            gatepass.send_approval_email()
            messages.success(
                self.request, 
                "Gatepass request submitted successfully and notifications sent to your parents"
            )
        except Exception as e:
            messages.warning(
                self.request, 
                f"Error processing your request: {str(e)}"
            )
            return self.form_invalid(form)
            
        return super().form_valid(form)

    def form_invalid(self, form):
        if not form.errors:
            messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Add Bootstrap classes to form fields
        for field in form.fields.values():
            if hasattr(field.widget, 'attrs'):
                field.widget.attrs.update({'class': 'form-control'})

class StudentGatepassListView(LoginRequiredMixin, ListView):
    model = Gatepass
    template_name = 'student_gatepass_list.html'
    context_object_name = 'gatepasses'
    paginate_by = 10

    def get_queryset(self):
        return Gatepass.objects.filter(
            student__profile=self.request.user.profile
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_gatepasses'] = Gatepass.objects.filter(
            student__profile=self.request.user.profile,
            status__in=['PENDING_PARENT', 'PENDING_WARDEN', 'APPROVED'],
            to_time__gte=timezone.now()
        ).order_by('from_time')
        return context