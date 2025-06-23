from django.contrib import admin
from .models import AbstractUser, Presensi

@admin.register(AbstractUser)
class AbstractUserAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'role', 'user')
    list_filter = ('role',)
    search_fields = ('first_name', 'last_name', 'user__username')
    ordering = ('first_name', 'last_name')

@admin.register(Presensi)
class PresensiAdmin(admin.ModelAdmin):
    list_display = ('user', 'tanggal', 'jam_masuk', 'jam_pulang', 'status')
    list_filter = ('status', 'tanggal', 'user__role')
    search_fields = ('user__first_name', 'user__last_name', 'keterangan')
    date_hierarchy = 'tanggal'
    ordering = ('-tanggal', '-jam_masuk')
