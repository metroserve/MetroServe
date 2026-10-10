import csv
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse
from django.shortcuts import render
from complaints.models import Complaint

def staff_test(user): return user.is_authenticated and user.is_staff

@user_passes_test(staff_test, login_url='/staff/login/')
def reports_dashboard(request):
    qs = Complaint.objects.all()
    total = qs.count()

    by_category = []
    for key, label in Complaint.CATEGORY_CHOICES:
        count = qs.filter(issue_type=key).count()
        percentage = (count / total * 100) if total else 0

        by_category.append({
            'label': label,
            'count': count,
            'percentage': percentage,
        })

    context = {
        'total': total,
        'pending': qs.filter(status='pending').count(),
        'progress': qs.filter(status='in_progress').count(),
        'resolved': qs.filter(status__in=['resolved', 'closed']).count(),
        'by_category': by_category,
    }

    return render(request, 'reports/dashboard.html', context)

@user_passes_test(staff_test, login_url='/staff/login/')
def export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="metroserve_complaints.csv"'
    writer = csv.writer(response); writer.writerow(['Reference','Citizen','Issue','Location','Status','Priority','Department','Created'])
    for c in Complaint.objects.select_related('citizen','department'):
        writer.writerow([c.reference_number,c.citizen.get_full_name() or c.citizen.username,c.get_issue_type_display(),c.location,c.get_status_display(),c.get_priority_display(),c.department.name if c.department else '',c.created_at.strftime('%Y-%m-%d %H:%M')])
    return response
