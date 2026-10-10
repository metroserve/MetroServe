from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from complaints.models import Complaint, Department
from notifications.models import Notification

def home(request):
    return render(request, 'dashboard/home.html')

@login_required
def citizen_dashboard(request):
    complaints = Complaint.objects.filter(citizen=request.user).select_related('department').order_by('-created_at')
    return render(request, 'dashboard/citizen_dashboard.html', {
        'total_complaints': complaints.count(),
        'active_complaints': complaints.exclude(status__in=['resolved','closed']).count(),
        'resolved_complaints': complaints.filter(status__in=['resolved','closed']).count(),
        'unread_notifications': Notification.objects.filter(citizen=request.user, is_read=False).count(),
        'recent_complaints': complaints[:6],
        'recent_notifications': Notification.objects.filter(citizen=request.user)[:4],
    })

def staff_test(user):
    return (
        user.is_authenticated
        and user.is_staff
        and not user.is_superuser
    )

@user_passes_test(staff_test, login_url='/staff/login/')
def staff_dashboard(request):
    qs = Complaint.objects.all()
    return render(request, 'dashboard/staff_dashboard.html', {
        'total': qs.count(), 'pending': qs.filter(status='pending').count(),
        'assigned': qs.filter(status='assigned').count(), 'progress': qs.filter(status='in_progress').count(),
        'resolved': qs.filter(status='resolved').count(), 'urgent': qs.filter(priority='urgent').exclude(status__in=['resolved','closed']).count(),
        'unassigned': qs.filter(assigned_to__isnull=True).exclude(status__in=['resolved','closed']).count(),
        'departments': Department.objects.all(),
        'recent': qs.select_related('citizen','department','assigned_to').order_by('-created_at')[:8],
    })


@user_passes_test(lambda user: user.is_authenticated and user.is_superuser, login_url='/admin/login/')
def admin_dashboard(request):
    qs = Complaint.objects.all()
    return render(request, 'dashboard/admin_dashboard.html', {
        'total': qs.count(),
        'open': qs.exclude(status__in=['resolved','closed']).count(),
        'urgent': qs.filter(priority='urgent').exclude(status__in=['resolved','closed']).count(),
        'resolved': qs.filter(status__in=['resolved','closed']).count(),
        'staff_count': __import__('django.contrib.auth.models', fromlist=['User']).User.objects.filter(is_staff=True).count(),
        'citizen_count': __import__('django.contrib.auth.models', fromlist=['User']).User.objects.filter(is_staff=False).count(),
        'departments': Department.objects.all(),
        'recent': qs.select_related('citizen','department').order_by('-created_at')[:10],
    })
