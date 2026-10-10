from io import BytesIO
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import send_mail
from django.core.files.base import ContentFile
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from .models import Complaint, ComplaintUpdate, Department
from notifications.models import Notification
from django.contrib.auth.models import User
from django.http import HttpResponseBadRequest

CATEGORY_DEPARTMENT = {
    'water': 'Water & Sanitation', 'sanitation': 'Water & Sanitation',
    'pothole': 'Roads & Infrastructure', 'streetlight': 'Electricity',
    'electricity': 'Electricity', 'waste': 'Waste Management',
    'traffic': 'Traffic & Transport', 'other': 'Community Services',
}

def staff_test(user):
    return (
        user.is_authenticated
        and user.is_staff
        and not user.is_superuser
    )


@login_required
def complaint_create(request):
    if request.method == 'POST':
        issue_type = request.POST.get('issue_type','')
        location = request.POST.get('location','').strip()
        description = request.POST.get('description','').strip()
        if not issue_type or not location or not description:
            messages.error(request, 'Please complete the issue type, location and description.')
            return render(request, 'complaints/create.html', {'categories': Complaint.CATEGORY_CHOICES})
        dept = Department.objects.filter(name=CATEGORY_DEPARTMENT.get(issue_type, 'Community Services')).first()
        with transaction.atomic():
            complaint = Complaint.objects.create(
                citizen=request.user, issue_type=issue_type, title=request.POST.get('title','Municipal service issue').strip() or 'Municipal service issue',
                location=location, latitude=request.POST.get('latitude') or None, longitude=request.POST.get('longitude') or None,
                description=description, priority=request.POST.get('priority','normal'), department=dept,
                image=request.FILES.get('image')
            )
           
            Notification.objects.create(citizen=request.user, complaint=complaint, title='Complaint submitted', message=f'{complaint.reference_number} was received by MetroServe.', channel='in_app')
        send_mail('MetroServe complaint received', f'Your reference number is {complaint.reference_number}.', None, [request.user.email], fail_silently=True)
        return render(request, 'complaints/success.html', {'complaint': complaint})
    return render(request, 'complaints/create.html', {'categories': Complaint.CATEGORY_CHOICES, 'priorities': Complaint.PRIORITY_CHOICES})

@login_required
def complaint_list(request):
    complaints = Complaint.objects.filter(citizen=request.user).select_related('department')
    return render(request, 'complaints/list.html', {'complaints': complaints})

@login_required
def complaint_detail(request, pk):
    complaint = get_object_or_404(Complaint.objects.select_related('department','assigned_to'), pk=pk, citizen=request.user)
    return render(request, 'complaints/detail.html', {'complaint': complaint})

@login_required(login_url='/login/')
def public_track(request, reference_number):
    complaint = get_object_or_404(
        Complaint.objects.select_related('department'),
        reference_number=reference_number,
        citizen=request.user,
    )
    return render(
        request,
        'complaints/public_track.html',
        {'complaint': complaint}
    )

@user_passes_test(staff_test, login_url='/staff/login/')
def staff_complaint_list(request):
    complaints = Complaint.objects.select_related('citizen','department','assigned_to').all()
    status = request.GET.get('status',''); priority = request.GET.get('priority',''); q = request.GET.get('q','')
    if status: complaints = complaints.filter(status=status)
    if priority: complaints = complaints.filter(priority=priority)
    if q: complaints = complaints.filter(reference_number__icontains=q) | complaints.filter(location__icontains=q) | complaints.filter(title__icontains=q)
    return render(request, 'dashboard/staff_queue.html', {'complaints': complaints, 'statuses': Complaint.STATUS_CHOICES, 'priorities': Complaint.PRIORITY_CHOICES})

@user_passes_test(staff_test, login_url='/staff/login/')
def staff_complaint_detail(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk)

    if request.method == 'POST':
        new_status = request.POST.get('status', complaint.status)
        new_priority = request.POST.get('priority', complaint.priority)
        note = request.POST.get('update_note', '').strip()
        resolution_notes = request.POST.get('resolution_notes', '').strip()
        assigned_id = request.POST.get('assigned_to') or None

        valid_statuses = dict(Complaint.STATUS_CHOICES)
        valid_priorities = dict(Complaint.PRIORITY_CHOICES)

        if new_status not in valid_statuses:
            return HttpResponseBadRequest('Invalid complaint status.')

        if new_priority not in valid_priorities:
            return HttpResponseBadRequest('Invalid complaint priority.')

        if assigned_id and not User.objects.filter(
            pk=assigned_id, is_staff=True
        ).exists():
            return HttpResponseBadRequest('Invalid staff assignment.')

        with transaction.atomic():
            complaint = Complaint.objects.select_for_update().get(pk=pk)
            old_status = complaint.status

            # Revalidate against the current database state.
            if new_status not in valid_statuses:
                return HttpResponseBadRequest('Invalid complaint status.')

            complaint.status = new_status
            complaint.priority = new_priority
            complaint.resolution_notes = resolution_notes
            complaint.assigned_to_id = assigned_id
            complaint.save()

            status_changed = old_status != new_status

            if status_changed or note:
                ComplaintUpdate.objects.create(
                    complaint=complaint,
                    previous_status=old_status if status_changed else '',
                    status=new_status,
                    note=note,
                    updated_by=request.user,
                )

            if status_changed:
                Notification.objects.create(
                    citizen=complaint.citizen,
                    complaint=complaint,
                    title='Complaint status changed',
                    message=(
                        f'{complaint.reference_number} changed from '
                        f'{valid_statuses[old_status]} to '
                        f'{valid_statuses[new_status]}.'
                    ),
                    channel='in_app',
                )

        messages.success(request, 'Complaint updated successfully.')
        return redirect('staff_complaint_detail', pk=pk)

    staff_users = User.objects.filter(
        is_staff=True
    ).order_by('first_name', 'last_name')

    return render(
        request,
        'dashboard/staff_detail.html',
        {
            'complaint': complaint,
            'statuses': Complaint.STATUS_CHOICES,
            'priorities': Complaint.PRIORITY_CHOICES,
            'staff_users': staff_users,
            'updates': complaint.updates.select_related('updated_by').all(),
        },
    )