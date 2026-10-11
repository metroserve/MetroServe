from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=20, default='#7c3aed')
    def __str__(self): return self.name

class Complaint(models.Model):
    CATEGORY_CHOICES = [('water','Water'),('sanitation','Sanitation'),('pothole','Road / Pothole'),('traffic','Traffic Light'),('waste','Waste Management'),('electricity','Electricity'),('streetlight','Street Lighting'),('other','Other')]
    PRIORITY_CHOICES = [('low','Low'),('normal','Normal'),('high','High'),('urgent','Urgent')]
    STATUS_CHOICES = [('pending','Pending'),('assigned','Assigned'),('in_progress','In Progress'),('resolved','Resolved'),('closed','Closed')]
    citizen = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaints')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='complaints')
    reference_number = models.CharField(max_length=30, unique=True, editable=False)
    issue_type = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    title = models.CharField(max_length=150, default='Municipal service issue')
    location = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    description = models.TextField()
    image = models.ImageField(upload_to='complaints/', blank=True, null=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    resolution_notes = models.TextField(blank=True)
    assigned_to = models.ForeignKey( User, on_delete=models.SET_NULL, null=True,blank=True,related_name='assigned_complaints',limit_choices_to={'is_staff': True})
    assigned_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.reference_number:
            year = timezone.now().year
            last = Complaint.objects.filter(reference_number__startswith=f'MET-{year}-').order_by('-id').first()
            next_num = int(last.reference_number.split('-')[-1]) + 1 if last else 1
            self.reference_number = f'MET-{year}-{next_num:05d}'
        super().save(*args, **kwargs)

    def tracking_url(self):
        return f'{settings.PUBLIC_BASE_URL}/track/{self.reference_number}/'

    def __str__(self): return f'{self.reference_number} - {self.get_issue_type_display()}'

class ComplaintUpdate(models.Model):
    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name='updates'
    )
    previous_status = models.CharField(
        max_length=20,
        choices=Complaint.STATUS_CHOICES,
        blank=True,
        default=''
    )
    status = models.CharField(
        max_length=20,
        choices=Complaint.STATUS_CHOICES
    )
    note = models.TextField(blank=True)
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.complaint.reference_number} - {self.get_status_display()}'
