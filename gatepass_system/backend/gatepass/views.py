from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import Student, Parent, Gatepass, Approval
from .serializers import StudentSerializer, ParentSerializer, GatepassSerializer, ApprovalSerializer
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone

class IsSecurity(BasePermission):
    """
    Allows access only to users with the Security role.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.profile.user_type == 'SECURITY'
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

# ----- Student APIs -----
class StudentListCreateAPIView(generics.ListCreateAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer

# ----- Gatepass APIs -----
class GatepassListCreateAPIView(generics.ListCreateAPIView):
    queryset = Gatepass.objects.all()
    serializer_class = GatepassSerializer
    permission_classes = [IsAuthenticated] # Ensure only logged-in users can create

    def perform_create(self, serializer):
        # Automatically associate the gatepass with the logged-in student.
        # This is more secure and correct.
        gatepass = serializer.save(student=self.request.user.profile.student)

        # Create Approval objects for all parents in sequence
        for i, parent in enumerate(gatepass.student.parents.all(), start=1):
            approval = Approval.objects.create(
                gatepass=gatepass,
                parent=parent,
                order=i
            )
            # If the parent has an email, send the notification
            if parent.email:
                self.send_approval_email(approval, self.request)

    def send_approval_email(self, approval, request):
        """
        Constructs and sends an approval request email to a parent.
        """
        gatepass = approval.gatepass
        student_name = gatepass.student.profile.user.get_full_name()
        
        # Build the unique approval/rejection URLs
        # In production, you would use settings to get the domain
        base_url = request.build_absolute_uri('/')[:-1] # http://127.0.0.1:8000
        approve_url = base_url + reverse('approval-action', kwargs={'token': approval.token_approve, 'action': 'approve'})
        reject_url = base_url + reverse('approval-action', kwargs={'token': approval.token_reject, 'action': 'reject'})

        subject = f"Gatepass Request for {student_name}"
        message = f"""
Hi {approval.parent.name},

Your child, {student_name}, has requested a gatepass with the following details:

Destination: {gatepass.destination}
Purpose: {gatepass.purpose}
From: {gatepass.from_time.strftime('%d %b %Y, %I:%M %p')}
To: {gatepass.to_time.strftime('%d %b %Y, %I:%M %p')}

Please click one of the links below to respond:
Approve: {approve_url}
Reject: {reject_url}

This request will expire in one hour.
"""
        send_mail(
            subject,
            message,
            'gatepass-system@yourcollege.edu',  # From email
            [approval.parent.email],          # To email
            fail_silently=False,
        )

# ----- Approval APIs -----
class ApprovalActionAPIView(APIView):
    """
    Parent approves or rejects using token in URL
    """
    def get(self, request, token, action):
        try:
            if action == "approve":
                approval = get_object_or_404(Approval, token_approve=token)
            elif action == "reject":
                approval = get_object_or_404(Approval, token_reject=token)
            else:
                return Response({"detail": "Invalid action."}, status=status.HTTP_400_BAD_REQUEST)
        except Approval.DoesNotExist:
            return Response({"detail": "Invalid token."}, status=status.HTTP_404_NOT_FOUND)

        if approval.status != "PENDING":
            return Response({"detail": "Already responded."}, status=status.HTTP_400_BAD_REQUEST)

        approval.status = "APPROVED" if action == "approve" else "REJECTED"
        approval.responded_at = timezone.now()
        approval.save()

        # Update gatepass status
        gatepass = approval.gatepass
        if approval.status == "REJECTED":
            gatepass.status = "REJECTED"
        elif all(a.status == "APPROVED" for a in gatepass.approvals.all()):
            gatepass.status = "APPROVED"
        gatepass.save()

        return Response({"detail": f"Gatepass {action}ed successfully."})
