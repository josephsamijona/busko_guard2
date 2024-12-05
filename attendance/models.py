from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import datetime, timedelta
from accounts.models import Employee

class Attendance(models.Model):
    ATTENDANCE_TYPES = [
        ('QR', 'QR Code'),
        ('NFC', 'NFC Card'),
        ('FACE', 'Face Recognition')
    ]
    
    STATUS_CHOICES = [
        ('PRESENT', 'Present'),
        ('LATE', 'Late'),
        ('ABSENT', 'Absent'),
        ('HALF_DAY', 'Half Day')
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)
    attendance_type = models.CharField(max_length=4, choices=ATTENDANCE_TYPES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    late_reason = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['employee', 'date']

class TemporaryQRCode(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    code = models.CharField(max_length=200, unique=True)
    purpose = models.CharField(max_length=50)  # check-in ou check-out
    expiry = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)

    def is_valid(self):
        return not self.is_used and self.expiry > datetime.now()
