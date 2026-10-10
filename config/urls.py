from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from accounts.views import citizen_login, register, staff_login, logout_view
from dashboard.views import home, citizen_dashboard, staff_dashboard, admin_dashboard
from complaints.views import public_track

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin-console/', admin_dashboard, name='admin_dashboard'),
    path('', home, name='home'),
    path('login/', citizen_login, name='login'),
    path('register/', register, name='register'),
    path('staff/login/', staff_login, name='staff_login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', citizen_dashboard, name='citizen_dashboard'),
    path('staff/', include('dashboard.urls')),
    path('complaints/', include('complaints.urls')),
    path('notifications/', include('notifications.urls')),
    path('profile/', include('accounts.urls')),
    path('reports/', include('reports.urls')),
    path('track/<str:reference_number>/', public_track, name='public_track'),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
