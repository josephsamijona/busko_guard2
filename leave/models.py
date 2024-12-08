from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import datetime, timedelta
from accounts.models import Employee, User
from django.core.exceptions import ValidationError

class Leave(models.Model):
    LEAVE_TYPES = [
        ('ANNUAL', 'Annual Leave'),
        ('SICK', 'Sick Leave'),
        ('UNPAID', 'Unpaid Leave'),
        ('OTHER', 'Other')
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled')
    ]

    employee = models.ForeignKey(
        Employee, 
        on_delete=models.CASCADE,
        related_name='leaves'
    )
    leave_type = models.CharField(
        max_length=10, 
        choices=LEAVE_TYPES,
        db_index=True
    )
    start_date = models.DateField(db_index=True)
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='PENDING',
        db_index=True
    )
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='approved_leaves'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Leave'
        verbose_name_plural = 'Leaves'
        permissions = [
            ("can_approve_leave", "Can approve leave requests"),
            ("can_reject_leave", "Can reject leave requests"),
        ]
        indexes = [
            models.Index(fields=['employee', 'status', 'start_date']),
            models.Index(fields=['leave_type', 'status']),
        ]

    def __str__(self):
        return f"{self.employee} - {self.get_leave_type_display()} ({self.start_date} to {self.end_date})"

    def days_count(self):
        """Calcule le nombre de jours de congé"""
        return (self.end_date - self.start_date).days + 1

    def clean(self):
        """Validation du modèle"""
        if self.start_date and self.end_date:
            # Validation des dates
            if self.start_date > self.end_date:
                raise ValidationError({'end_date': 'La date de fin doit être postérieure à la date de début.'})

    def save(self, *args, **kwargs):
        # Si le statut change pour approuvé, enregistrer la date d'approbation
        if self.status == 'APPROVED' and not self.approved_at:
            self.approved_at = timezone.now()
        
        self.full_clean()
        super().save(*args, **kwargs)

class LeaveBalance(models.Model):
    employee = models.ForeignKey(
        Employee, 
        on_delete=models.CASCADE,
        related_name='leave_balances'
    )
    leave_type = models.CharField(
        max_length=10, 
        choices=Leave.LEAVE_TYPES,
        db_index=True
    )
    year = models.IntegerField(
        validators=[MinValueValidator(2000), MaxValueValidator(2100)],
        db_index=True
    )
    total_days = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )
    used_days = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )
    
    class Meta:
        unique_together = ['employee', 'leave_type', 'year']
        ordering = ['-year', 'leave_type']
        verbose_name = 'Leave Balance'
        verbose_name_plural = 'Leave Balances'
        indexes = [
            models.Index(fields=['employee', 'year']),
        ]

    def __str__(self):
        return f"{self.employee} - {self.get_leave_type_display()} ({self.year})"

    def remaining_days(self):
        """Calcule les jours restants"""
        return max(0, self.total_days - self.used_days)

    def clean(self):
        """Validation du modèle"""
        if self.used_days > self.total_days:
            raise ValidationError({'used_days': 'Le nombre de jours utilisés ne peut pas dépasser le total.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def get_leave_type_display(self):
        """Retourne le libellé du type de congé"""
        return dict(Leave.LEAVE_TYPES)[self.leave_type]