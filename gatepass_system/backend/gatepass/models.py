# from django.db import models

# Create your models here.
from django.db import models
from django.utils import timezone

class Student(models.Model):
    name = models.CharField(max_length=100)
    roll_no = models.CharField(max_length=20)
    email = models.EmailField()
    parent_contact = models.CharField(max_length=20)

class GatepassRequest(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Expired', 'Expired'),
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    destination = models.CharField(max_length=200)
    purpose = models.TextField()
    date_time = models.DateTimeField()
    duration = models.IntegerField()  # in hours
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(default=timezone.now)
