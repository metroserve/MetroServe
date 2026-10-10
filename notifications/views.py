from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from .models import Notification, NotificationPreference

@login_required
def notification_list(request):
    notifications = Notification.objects.filter(citizen=request.user)
    return render(request, 'notifications/list.html', {'notifications': notifications})

@login_required
def notification_detail(request, pk):
    n = get_object_or_404(Notification, pk=pk, citizen=request.user)
    n.is_read = True; n.save(update_fields=['is_read'])
    return render(request, 'notifications/detail.html', {'notification': n})

@login_required
def notification_preferences(request):
    preference, _ = NotificationPreference.objects.get_or_create(citizen=request.user)
    if request.method == 'POST':
        value = request.POST.get('preferred_channel')
        if value in dict(Notification.CHANNEL_CHOICES):
            preference.preferred_channel = value; preference.save()
            messages.success(request, 'Notification preference saved.')
    return render(request, 'notifications/preferences.html', {'preference': preference, 'choices': Notification.CHANNEL_CHOICES})
