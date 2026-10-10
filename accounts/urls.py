from django.urls import path
from .views import profile, verify_email_code

urlpatterns = [
    path('', profile, name='profile'),
    path('verify-email/', verify_email_code, name='verify_email_code'),
]
