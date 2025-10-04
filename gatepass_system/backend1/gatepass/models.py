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
    from_time = models.DateTimeField(default=timezone.now)
    to_time = models.DateTimeField(default=timezone.now)
    destination = models.CharField(max_length=255)
    purpose = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING_PARENT")
    created_at = models.DateTimeField(auto_now_add=True)
    # Gatepass request expires in 1 hour if not approved/rejected
    request_expires_at = models.DateTimeField(blank=True, null=True)
    actual_exit_time = models.DateTimeField(null=True, blank=True)
    actual_entry_time = models.DateTimeField(null=True, blank=True)
    audit = models.JSONField(default=list, blank=True)  # list of events

    def save(self, *args, **kwargs):
        # default expiry: 1 hour after creation if not set
        if not self.request_expires_at:
            self.request_expires_at = timezone.now() + timezone.timedelta(hours=1)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student} - {self.destination} ({self.status})"


class Approval(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    ]
    gatepass = models.ForeignKey(Gatepass, on_delete=models.CASCADE, related_name="approvals")
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)  # sequential approval
    token_approve = models.UUIDField(default=uuid.uuid4, editable=False)
    token_reject = models.UUIDField(default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("gatepass", "parent")
        ordering = ["order"]

    def __str__(self):
        return f"Approval: {self.gatepass.id} - {self.parent.name} ({self.status})"
