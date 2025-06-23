from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import time

class AbstractUser(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('guru', 'Guru'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='abstract_user')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='guru')
    nip = models.CharField(max_length=20, unique=True, null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Presensi(models.Model):
    STATUS_CHOICES = [
        ('hadir', 'Hadir'),
        ('izin', 'Izin'),
        ('sakit', 'Sakit'),
        ('alpha', 'Alpha'),
        ('terlambat', 'Terlambat'),
    ]
    
    user = models.ForeignKey(AbstractUser, on_delete=models.CASCADE, related_name='presensi')
    tanggal = models.DateField(default=timezone.now)
    jam_masuk = models.TimeField()
    jam_pulang = models.TimeField(null=True, blank=True)
    image_checkin = models.ImageField(upload_to='presensi_images/', null=True, blank=True)
    image_checkout = models.ImageField(upload_to='presensi_images/', null=True, blank=True) 
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='hadir')
    keterangan = models.TextField(blank=True, null=True)
    terlambat_menit = models.IntegerField(default=0)
    jam_kerja_efektif = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    lokasi_checkin = models.CharField(max_length=255, null=True, blank=True)
    lokasi_checkout = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        ordering = ['-tanggal', '-jam_masuk']

    def __str__(self):
        return f"{self.user.full_name} - {self.tanggal}"

    def save(self, *args, **kwargs):
        # Calculate late minutes if check-in time is after 07:00
        if self.jam_masuk and self.jam_masuk > time(7, 0):
            from datetime import datetime
            checkin_time = datetime.combine(datetime.today(), self.jam_masuk)
            target_time = datetime.combine(datetime.today(), time(7, 0))
            self.terlambat_menit = int((checkin_time - target_time).total_seconds() / 60)
            
            if self.terlambat_menit > 0:
                self.status = 'terlambat'
        
        # Calculate effective work hours
        if self.jam_masuk and self.jam_pulang:
            from datetime import datetime
            checkin = datetime.combine(datetime.today(), self.jam_masuk)
            checkout = datetime.combine(datetime.today(), self.jam_pulang)
            work_hours = (checkout - checkin).total_seconds() / 3600
            self.jam_kerja_efektif = round(work_hours, 2)
        
        super().save(*args, **kwargs)


class PengajuanIzin(models.Model):
    JENIS_IZIN_CHOICES = [
        ('izin', 'Izin'),
        ('sakit', 'Sakit'),
        ('cuti', 'Cuti'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('disetujui', 'Disetujui'),
        ('ditolak', 'Ditolak'),
    ]

    user = models.ForeignKey(AbstractUser, on_delete=models.CASCADE, related_name='pengajuan_izin')
    jenis_izin = models.CharField(max_length=20, choices=JENIS_IZIN_CHOICES, default='izin')
    tanggal_mulai = models.DateField()
    tanggal_selesai = models.DateField()
    keterangan = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    alasan_penolakan = models.TextField(blank=True, null=True)
    tanggal_pengajuan = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    tanggal_approval = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(AbstractUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_pengajuan')

    class Meta:
        ordering = ['-tanggal_pengajuan']

    def __str__(self):
        return f"{self.user.full_name} - {self.tanggal_mulai} s/d {self.tanggal_selesai}"


class JamKerja(models.Model):
    """Model untuk mengatur jam kerja standar"""
    jam_masuk = models.TimeField(default=time(7, 0))
    jam_pulang = models.TimeField(default=time(15, 0))
    toleransi_terlambat = models.IntegerField(default=15)  # dalam menit
    
    class Meta:
        verbose_name_plural = "Jam Kerja"
    
    def __str__(self):
        return f"Jam Kerja: {self.jam_masuk} - {self.jam_pulang}"
