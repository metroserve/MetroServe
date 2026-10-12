from django.urls import path

from . import views

urlpatterns = [
    path('', views.profile, name='profile'),
    path('register/', views.register, name='register'),
    path('login/', views.citizen_login, name='login'),
    path('staff/login/', views.staff_login, name='staff_login'),
    path('logout/', views.logout_view, name='logout'),
    path('verify-email/', views.verify_email_code, name='verify_email_code'),
]
