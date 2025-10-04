import uuid
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class Profile(models.Model):
    USER_TYPE_CHOICES = [
        ("STUDENT", "Student"),
        ("PARENT", "Parent"),
        ("WARDEN", "Warden"),
        ("SECURITY", "Security"),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)

    def __str__(self):
        return f"{self.user.username} - {self.get_user_type_display()}"

class Student(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, null=True)
    roll_no = models.CharField(max_length=50, unique=True)
    parents = models.ManyToManyField("Parent", related_name="children")

    def __str__(self):
        if self.profile and self.profile.user:
            return f"{self.profile.user.get_full_name() or self.profile.user.username} ({self.roll_no})"
        return f"Student ({self.roll_no})"


class Parent(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Gatepass(models.Model):
    STATUS_CHOICES = [
        ("PENDING_PARENT", "Pending Parent Approval"),
        ("PENDING_WARDEN", "Pending Warden Approval"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
        ("EXPIRED", "Expired"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="gatepasses")
    purpose = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)
    from_time = models.DateTimeField()
    to_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING_PARENT")
    created_at = models.DateTimeField(auto_now_add=True)
    request_expires_at = models.DateTimeField(null=True, blank=True)
    actual_exit_time = models.DateTimeField(null=True, blank=True)
    actual_entry_time = models.DateTimeField(null=True, blank=True)
    audit = models.JSONField(default=list, blank=True)

    def save(self, *args, **kwargs):
        # Set request expiry if not set and status is PENDING_PARENT
        if not self.request_expires_at and self.status == "PENDING_PARENT":
            self.request_expires_at = timezone.now() + timezone.timedelta(hours=1)
        super().save(*args, **kwargs)

    def send_approval_email(self):
        from django.core.mail import send_mail
        from django.conf import settings
        from django.urls import reverse

        student_name = self.student.profile.user.get_full_name() or self.student.profile.user.username
        
        # Create approval token
        token = ApprovalToken.objects.create(
            gatepass=self,
            expires_at=self.request_expires_at
        )

        for parent in self.student.parents.all():
            subject = f"Gatepass Request from {student_name}"
            message = f"""
Dear {parent.name},

Your child, {student_name}, has requested a gatepass with the following details:

Destination: {self.destination}
Purpose: {self.purpose}
From: {timezone.localtime(self.from_time).strftime('%d %b %Y, %I:%M %p')}
To: {timezone.localtime(self.to_time).strftime('%d %b %Y, %I:%M %p')}

To approve or reject this request, please click one of these links:

Approve: {settings.SITE_URL}{reverse('approval-action', kwargs={'token': token.token, 'action': 'approve'})}
Reject: {settings.SITE_URL}{reverse('approval-action', kwargs={'token': token.token, 'action': 'reject'})}

This approval link will expire in {timezone.timedelta(hours=1)} hours.

Best regards,
Gatepass System
"""
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [parent.email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Failed to send email to {parent.email}: {str(e)}")

    def get_status_color(self):
        return {
            'PENDING_PARENT': 'warning',
            'PENDING_WARDEN': 'info',
            'APPROVED': 'success',
            'REJECTED': 'danger',
            'EXPIRED': 'secondary',
        }.get(self.status, 'primary')


class ApprovalToken(models.Model):
    token = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    gatepass = models.ForeignKey(Gatepass, on_delete=models.CASCADE, related_name='approval_tokens')
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE, related_name='approval_tokens')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    used = models.BooleanField(default=False)
    action_taken = models.CharField(max_length=10, choices=[('approve', 'Approved'), ('reject', 'Rejected')], null=True, blank=True)

    @property
    def is_valid(self):
        return not self.used and self.expires_at > timezone.now()

    def use_token(self, action):
        if self.is_valid and action in ['approve', 'reject']:
            self.used = True
            self.used_at = timezone.now()
            self.action_taken = action
            self.save()
            return True
        return False

    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Token expires in 1 hour by default (same as gatepass request)
            self.expires_at = timezone.now() + timezone.timedelta(hours=1)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']

