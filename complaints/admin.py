from django.contrib import admin
from django.db import transaction

from .models import Complaint, ComplaintUpdate, Department


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'color')


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = (
        'reference_number',
        'title',
        'status',
        'priority',
        'assigned_to',
        'updated_at',
    )
    list_filter = ('status', 'priority', 'department')
    search_fields = ('reference_number', 'title', 'location')

    def save_model(self, request, obj, form, change):
        previous_status = None

        if change and obj.pk:
            previous_status = (
                Complaint.objects
                .get(pk=obj.pk)
                .status
            )

        with transaction.atomic():
            super().save_model(request, obj, form, change)

            if (
                previous_status is not None
                and previous_status != obj.status
            ):
                ComplaintUpdate.objects.create(
                    complaint=obj,
                    previous_status=previous_status,
                    status=obj.status,
                    note='Status changed via Django Admin.',
                    updated_by=request.user,
                )


@admin.register(ComplaintUpdate)
class ComplaintUpdateAdmin(admin.ModelAdmin):
    list_display = (
        'complaint',
        'previous_status',
        'status',
        'updated_by',
        'created_at',
    )
    list_filter = ('status', 'created_at')
    search_fields = (
        'complaint__reference_number',
        'updated_by__username',
    )
    readonly_fields = (
        'complaint',
        'previous_status',
        'status',
        'note',
        'updated_by',
        'created_at',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
