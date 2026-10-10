from django.urls import path
from .views import reports_dashboard, export_csv
urlpatterns = [path('', reports_dashboard, name='reports_dashboard'), path('export/csv/', export_csv, name='export_complaints_csv')]
