"""
URL configuration for dash project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from presensi import views
from django.conf.urls.static import static

urlpatterns = (
    [
        path('', views.home, name='home'),
        path('admin/', admin.site.urls),
        path('login/', views.login, name='login'),
        path('logout/', views.logout, name='logout'),
        
        # Admin URLs
        path('analisa-absensi/', views.analisa_absensi, name='analisa_absensi'),
        path('daftar-guru/', views.daftar_guru, name='daftar_guru'),
        path('ubah-password-guru/', views.ubah_password_guru, name='ubah_password_guru'),
        path('list-pengajuan/', views.list_pengajuan, name='list_pengajuan'),
        
        # Teacher URLs
        path('absensi/', views.absensi, name='absensi'),
        path('history-absensi/', views.history_absensi, name='history_absensi'),
        path('pengajuan/', views.pengajuan, name='pengajuan'),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)
