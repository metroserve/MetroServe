from django.contrib.auth.models import User
from django.db import models
from complaints.models import Complaint

class Notification(models.Model):
    CHANNEL_CHOICES = [('in_app','In-App'),('email','Email'),('sms','SMS'),('phone','Phone')]
    citizen = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    title = models.CharField(max_length=200)
    message = models.TextField()
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default='in_app')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['-created_at']

class NotificationPreference(models.Model):
    citizen = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preference')
    preferred_channel = models.CharField(max_length=20, choices=Notification.CHANNEL_CHOICES, default='in_app')
    updated_at = models.DateTimeField(auto_now=True)
