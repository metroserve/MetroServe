from django.urls import path
from . import views
urlpatterns = [
    path('report/', views.complaint_create, name='complaint_create'),
    path('my/', views.complaint_list, name='complaint_list'),
    path('<int:pk>/', views.complaint_detail, name='complaint_detail'),
    path('staff/', views.staff_complaint_list, name='staff_complaint_list'),
    path('staff/<int:pk>/', views.staff_complaint_detail, name='staff_complaint_detail'),
]
