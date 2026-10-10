from django.urls import path
from .views import staff_dashboard
from complaints.views import staff_complaint_list, staff_complaint_detail
urlpatterns = [
    path('', staff_dashboard, name='staff_dashboard'),
    path('complaints/', staff_complaint_list, name='staff_complaint_list'),
    path('complaints/<int:pk>/', staff_complaint_detail, name='staff_complaint_detail'),
]
