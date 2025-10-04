from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import View, TemplateView
from .models import Student, Parent, Gatepass, ApprovalToken
from .serializers import StudentSerializer, ParentSerializer, GatepassSerializer
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import logout
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

from django.shortcuts import redirect

def redirect_after_login(request):
    if request.user.is_authenticated:
        try:
            user_type = request.user.profile.user_type
            if user_type == 'STUDENT':
                return redirect('student-gatepass-list')
            elif user_type == 'WARDEN':
                return redirect('warden-dashboard')
            elif user_type == 'PARENT':
                return redirect('parent-dashboard')
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
    permission_classes = [IsAuthenticated, IsWarden]

class WardenGatepassActionAPIView(APIView):
    permission_classes = [IsAuthenticated, IsWarden]

    def post(self, request, pk, action):
        gatepass = get_object_or_404(Gatepass, pk=pk)

        if gatepass.status != 'PENDING_WARDEN_APPROVAL':
            return Response({"detail": "Gatepass is not pending warden approval."}, status=status.HTTP_400_BAD_REQUEST)

        if action == "approve":
            gatepass.status = "APPROVED"
        elif action == "reject":
            gatepass.status = "REJECTED"
        else:
            return Response({"detail": "Invalid action."}, status=status.HTTP_400_BAD_REQUEST)

        # Log the warden's action
        gatepass.audit.append({
            "action": f"Warden {action}d",
            "user": request.user.username,
            "timestamp": timezone.now().isoformat(),
        })
        gatepass.save()
        return Response({"detail": f"Gatepass {action}d successfully."})


# ----- Warden Views -----
class WardenDashboardView(View):
    def get(self, request):
        pending_gatepasses = Gatepass.objects.filter(status='PENDING_WARDEN_APPROVAL').order_by('-created_at')
        return render(request, 'warden_dashboard.html', {'gatepasses': pending_gatepasses})

# ----- Student Views -----
class StudentRequestView(View):
    def get(self, request):
        if not hasattr(request.user, 'profile') or request.user.profile.user_type != 'STUDENT':
            return redirect('login')
        return render(request, 'student_request.html')

    def post(self, request):
        if not hasattr(request.user, 'profile') or request.user.profile.user_type != 'STUDENT':
            return redirect('login')

        try:
            student = request.user.profile.student
            from_time = timezone.datetime.strptime(request.POST['from_time'], '%Y-%m-%dT%H:%M')
            to_time = timezone.datetime.strptime(request.POST['to_time'], '%Y-%m-%dT%H:%M')

            # Make times timezone-aware
            from_time = timezone.make_aware(from_time)
            to_time = timezone.make_aware(to_time)

            # Validate times
            if from_time >= to_time:
                messages.error(request, "From time must be before to time")
                return redirect('student-request')
            
            if from_time < timezone.now():
                messages.error(request, "From time must be in the future")
                return redirect('student-request')

            # Create gatepass
            gatepass = Gatepass.objects.create(
                student=student,
                destination=request.POST['destination'],
                purpose=request.POST['purpose'],
                from_time=from_time,
                to_time=to_time,
                status='PENDING_PARENT'
            )

            # Send approval email to parents
            gatepass.send_approval_email()
            messages.success(request, "Gatepass request submitted successfully. Your parents will be notified.")

        except Exception as e:
            messages.error(request, f"Error submitting request: {str(e)}")
            return redirect('student-request')

        return redirect('student-gatepass-list')

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
                # Check if all parents have approved
                all_approved = True
                for parent in gatepass.student.parents.all():
                    latest_token = parent.approval_tokens.filter(
                        gatepass=gatepass,
                        used=True
                    ).order_by('-created_at').first()
                    
                    if not latest_token or latest_token.action_taken != 'approve':
                        all_approved = False
                        break
                
                if all_approved:
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
