from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import View, TemplateView
from .models import Student, Parent, Gatepass, ApprovalToken
from .serializers import StudentSerializer, ParentSerializer, GatepassSerializer
from .forms import GatepassRequestForm
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.views import LogoutView

class IndexView(TemplateView):
    template_name = 'index.html'

class CustomLogoutView(LogoutView):
    next_page = '/'  # Redirect to home page after logout

class StudentListCreateAPIView(generics.ListCreateAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]

from django.contrib.auth.views import LoginView

class UserLoginView(LoginView):
    template_name = 'registration/login.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pass the role query parameter to the template for pre-selection
        context['selected_role'] = self.request.GET.get('role', '').upper()
        return context

    def form_valid(self, form):
        user = form.get_user()
        # Check POST data first, then query parameter as fallback
        selected_role = self.request.POST.get('user_type') or self.request.GET.get('role')

        try:
            user_type = user.profile.user_type
            if user_type != selected_role.upper():
                form.add_error(None, "Invalid role selected for this account.")
                return self.form_invalid(form)

            # Login the user
            response = super().form_valid(form)

            # Store role in session
            self.request.session['user_role'] = user_type

            # Redirect based on role
            redirect_urls = {
                'STUDENT': 'student-gatepass-list',
                'WARDEN': 'warden-dashboard',
                'SECURITY': 'security-dashboard'
            }

            return redirect(redirect_urls.get(user_type, 'login'))

        except AttributeError:
            form.add_error(None, "User profile not found.")
            return self.form_invalid(form)

from django.shortcuts import redirect

def redirect_after_login(request):
    if request.user.is_authenticated:
        try:
            user_type = request.user.profile.user_type
            if user_type == 'STUDENT':
                return redirect('student-gatepass-list')
            elif user_type == 'WARDEN':
                return redirect('warden-dashboard')
            elif user_type == 'SECURITY':
                return redirect('security-dashboard')
        except AttributeError:
            # If user doesn't have a profile
            return redirect('login')
    return redirect('login')

class IsSecurity(BasePermission):
    """
    Allows access only to users with the Security role.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.profile.user_type == 'SECURITY'

class SecurityDashboardView(View):
    def get(self, request):
        gatepass_id = request.GET.get('gatepass_id')
        gatepass = None
        if gatepass_id:
            try:
                gatepass = Gatepass.objects.get(id=gatepass_id)
            except (Gatepass.DoesNotExist, ValueError):
                gatepass = None
        return render(request, 'security_dashboard.html', {'gatepass': gatepass})

# ----- Security APIs -----
class SecurityGatepassDetailAPIView(generics.RetrieveAPIView):
    """
    Retrieve a single gatepass for verification.
    """
    queryset = Gatepass.objects.all()
    serializer_class = GatepassSerializer
    permission_classes = [IsAuthenticated, IsSecurity]
    lookup_field = 'id' # The gatepass UUID

class SecurityLogTimeAPIView(APIView):
    """
    Log the student's exit or entry time.
    """
    permission_classes = [IsAuthenticated, IsSecurity]

    def post(self, request, pk, action):
        gatepass = get_object_or_404(Gatepass, pk=pk)

        if action == 'exit' and gatepass.status == 'APPROVED' and not gatepass.actual_exit_time:
            gatepass.actual_exit_time = timezone.now()
            gatepass.save()
            return Response({"detail": "Exit time logged."})

        if action == 'entry' and gatepass.actual_exit_time and not gatepass.actual_entry_time:
            gatepass.actual_entry_time = timezone.now()
            gatepass.save()
            return Response({"detail": "Entry time logged."})

        return Response({"detail": "Invalid action or state."}, status=status.HTTP_400_BAD_REQUEST)

class IsWarden(BasePermission):
    """
    Allows access only to users with the Warden role.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.profile.user_type == 'WARDEN'

# ----- Warden APIs -----
class WardenGatepassListAPIView(generics.ListAPIView):
    queryset = Gatepass.objects.select_related('student__profile__user').prefetch_related('approvals__parent').all().order_by('-created_at')
    serializer_class = GatepassSerializer
    permission_classes = [IsWarden]
    authentication_classes = [SessionAuthentication]

class WardenGatepassActionAPIView(APIView):
    permission_classes = [IsWarden]
    authentication_classes = [SessionAuthentication]

    def post(self, request, pk, action):
        gatepass = get_object_or_404(Gatepass, pk=pk)

        if action not in ["approve", "reject"]:
            return Response({"detail": "Invalid action."}, status=status.HTTP_400_BAD_REQUEST)

        old_status = gatepass.status
        is_override = old_status != 'PENDING_WARDEN'

        if action == "approve":
            gatepass.status = "APPROVED"
        elif action == "reject":
            gatepass.status = "REJECTED"

        # Log the warden's action with override flag
        gatepass.audit.append({
            "action": f"Warden {action}d" + (" (override)" if is_override else ""),
            "old_status": old_status,
            "user": request.user.username,
            "timestamp": timezone.now().isoformat(),
        })
        gatepass.save()
        return Response({
            "detail": f"Gatepass {action}d successfully." + (" (Override)" if is_override else ""),
            "was_override": is_override
        })


# ----- Warden Views -----
class WardenDashboardView(View):
    def get(self, request):
        pending_gatepasses = Gatepass.objects.filter(status='PENDING_WARDEN').order_by('-created_at')
        return render(request, 'warden_dashboard.html', {'gatepasses': pending_gatepasses})

# ----- Student Views -----
class StudentRequestView(View):
    def get(self, request):
        if not hasattr(request.user, 'profile') or request.user.profile.user_type != 'STUDENT':
            return redirect('login')
        form = GatepassRequestForm()
        recent_requests = Gatepass.objects.filter(student=request.user.profile.student).order_by('-created_at')[:5]
        return render(request, 'student_request.html', {'form': form, 'recent_requests': recent_requests})

    def post(self, request):
        if not hasattr(request.user, 'profile') or request.user.profile.user_type != 'STUDENT':
            return redirect('login')

        form = GatepassRequestForm(request.POST)
        recent_requests = Gatepass.objects.filter(student=request.user.profile.student).order_by('-created_at')[:5]

        if form.is_valid():
            try:
                gatepass = form.save(commit=False)
                gatepass.student = request.user.profile.student
                gatepass.status = 'PENDING_PARENT'
                gatepass.save()

                # Send approval email to parents
                gatepass.send_approval_email()
                messages.success(request, "Gatepass request submitted successfully. Your parents will be notified.")
                return redirect('student-gatepass-list')
            except Exception as e:
                messages.error(request, f"Error submitting request: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")

        return render(request, 'student_request.html', {'form': form, 'recent_requests': recent_requests})

class StudentGatepassListView(View):
    def get(self, request):
        student = request.user.profile.student
        gatepasses = Gatepass.objects.filter(student=student).order_by('-created_at')
        return render(request, 'student_gatepass_list.html', {'gatepasses': gatepasses})

# ----- Gatepass APIs -----
class GatepassListCreateAPIView(generics.ListCreateAPIView):
    queryset = Gatepass.objects.all()
    serializer_class = GatepassSerializer
    permission_classes = [IsAuthenticated] # Ensure only logged-in users can create

    def perform_create(self, serializer):
        # Automatically associate the gatepass with the logged-in student
        if not hasattr(self.request.user, 'profile') or self.request.user.profile.user_type != 'STUDENT':
            raise serializers.ValidationError("Only students can create gatepass requests")
            
        gatepass = serializer.save(student=self.request.user.profile.student)
        
        try:
            # Send approval emails
            gatepass.send_approval_email()
        except Exception as e:
            # Log the error but don't fail the request
            print(f"Error sending approval emails: {str(e)}")

# ----- Approval APIs -----
class ApprovalActionAPIView(APIView):
    """
    Parent approves or rejects using token in URL
    """
    def get(self, request, token, action):
        try:
            approval_token = get_object_or_404(ApprovalToken, token=token)
            
            if not approval_token.is_valid:
                return Response({"detail": "This approval link has expired or already been used."}, 
                             status=status.HTTP_400_BAD_REQUEST)
            
            if action not in ['approve', 'reject']:
                return Response({"detail": "Invalid action."}, 
                             status=status.HTTP_400_BAD_REQUEST)
                
            # Use the token
            success = approval_token.use_token(action)
            if not success:
                return Response({"detail": "Could not process approval action."}, 
                             status=status.HTTP_400_BAD_REQUEST)

            # Update gatepass status
            gatepass = approval_token.gatepass
            if action == 'reject':
                gatepass.status = "REJECTED"
            else:
                # Just one parent approval is enough - move to warden
                gatepass.status = "PENDING_WARDEN"
                    
            gatepass.save()
            
            # Record the action in audit log
            gatepass.audit.append({
                "action": f"Parent {action}d",
                "parent": approval_token.parent.name,
                "timestamp": timezone.now().isoformat(),
            })
            gatepass.save()

            return Response({
                "detail": f"Gatepass request {action}ed successfully.",
                "status": gatepass.status
            })
        except ApprovalToken.DoesNotExist:
            return Response({"detail": "Invalid approval token."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
