from django.urls import path
from .views import notification_list, notification_detail, notification_preferences
urlpatterns = [
    path('', notification_list, name='notification_list'),
    path('preferences/', notification_preferences, name='notification_preferences'),
    path('<int:pk>/', notification_detail, name='notification_detail'),
]
