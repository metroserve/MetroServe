from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('citizen', 'Citizen'),
        ('staff', 'Municipal Staff'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    phone_number = models.CharField(max_length=30, blank=True)
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='citizen'
    )
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        blank=True,
        null=True
    )
    bio = models.CharField(max_length=255, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return (
            f'{self.user.get_full_name() or self.user.username} '
            f'- {self.get_role_display()}'
        )


class EmailVerificationCode(models.Model):
    PURPOSE_CHOICES = [
        ('registration', 'Registration'),
        ('login', 'Login'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='email_verification_codes'
    )
    purpose = models.CharField(
        max_length=20,
        choices=PURPOSE_CHOICES
    )
    code_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    used_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.user.username} - {self.purpose}'