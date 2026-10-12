from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class UserProfile(models.Model):
    ROLE_CHOICES = [('citizen', 'Citizen'), ('staff', 'Municipal Staff')]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile'
    )
    phone_number = models.CharField(max_length=30, blank=True)
    role = models.CharField(
        max_length=20, choices=ROLE_CHOICES, default='citizen'
    )
    profile_picture = models.ImageField(
        upload_to='profile_pictures/', blank=True, null=True
    )
    bio = models.CharField(max_length=255, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return (
            f'{self.user.get_full_name() or self.user.username}'
            f' - {self.get_role_display()}'
        )


class EmailVerificationCode(models.Model):
    PURPOSE_CHOICES = [
        ('registration', 'Registration'),
        ('login', 'Login'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='email_verification_codes',
    )
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    code_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    used_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'purpose', 'used_at']),
        ]

    def __str__(self):
        state = 'used' if self.used_at else 'active'
        return f'{self.user.username} - {self.purpose} - {state}'

    def is_expired(self):
        return timezone.now() >= self.expires_at

    def is_usable(self):
        return self.used_at is None and not self.is_expired()