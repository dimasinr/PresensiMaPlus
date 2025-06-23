from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
from presensi.models import AbstractUser, Presensi, PengajuanIzin, JamKerja
import random

class Command(BaseCommand):
    help = 'Generate sample data for testing the attendance system'

    def handle(self, *args, **options):
        self.stdout.write('Generating sample data...')
        
        # Create admin user if not exists
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_user(
                username='admin',
                email='admin@sekolah.id',
                password='admin123'
            )
            AbstractUser.objects.create(
                user=admin_user,
                first_name='Admin',
                last_name='Sistem',
                role='admin',
                nip='ADM001',
                phone='08123456789'
            )
            self.stdout.write('Admin user created')
        
        # Create sample teachers
        teachers_data = [
            {'first_name': 'Ahmad', 'last_name': 'Rizki', 'nip': 'GUR001', 'email': 'ahmad@sekolah.id'},
            {'first_name': 'Siti', 'last_name': 'Nurhaliza', 'nip': 'GUR002', 'email': 'siti@sekolah.id'},
            {'first_name': 'Budi', 'last_name': 'Santoso', 'nip': 'GUR003', 'email': 'budi@sekolah.id'},
            {'first_name': 'Dewi', 'last_name': 'Kartika', 'nip': 'GUR004', 'email': 'dewi@sekolah.id'},
            {'first_name': 'Rudi', 'last_name': 'Hartono', 'nip': 'GUR005', 'email': 'rudi@sekolah.id'},
        ]
        
        for teacher_data in teachers_data:
            if not User.objects.filter(username=teacher_data['nip']).exists():
                user = User.objects.create_user(
                    username=teacher_data['nip'],
                    email=teacher_data['email'],
                    password='guru123'
                )
                AbstractUser.objects.create(
                    user=user,
                    first_name=teacher_data['first_name'],
                    last_name=teacher_data['last_name'],
                    role='guru',
                    nip=teacher_data['nip'],
                    phone=f'08{random.randint(100000000, 999999999)}'
                )
                self.stdout.write(f'Teacher {teacher_data["first_name"]} {teacher_data["last_name"]} created')
        
        # Create sample attendance records for the last 30 days
        teachers = AbstractUser.objects.filter(role='guru')
        today = timezone.now().date()
        
        for teacher in teachers:
            for i in range(30):
                date = today - timedelta(days=i)
                
                # Skip weekends
                if date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                    continue
                
                # Random attendance status
                status_choices = ['hadir', 'hadir', 'hadir', 'terlambat', 'izin', 'sakit', 'alpha']
                status = random.choice(status_choices)
                
                if status in ['hadir', 'terlambat']:
                    # Generate check-in time
                    if status == 'hadir':
                        hour = random.randint(6, 7)  # 6:00 - 7:59
                    else:  # terlambat
                        hour = random.randint(8, 9)  # 8:00 - 9:59
                    
                    minute = random.randint(0, 59)
                    checkin_time = datetime.combine(date, datetime.min.time().replace(hour=hour, minute=minute))
                    
                    # Generate check-out time
                    checkout_hour = random.randint(14, 16)  # 14:00 - 16:59
                    checkout_minute = random.randint(0, 59)
                    checkout_time = datetime.combine(date, datetime.min.time().replace(hour=checkout_hour, minute=checkout_minute))
                    
                    # Calculate work hours
                    work_hours = (checkout_time - checkin_time).total_seconds() / 3600
                    
                    # Calculate late minutes
                    late_minutes = 0
                    if status == 'terlambat':
                        standard_time = datetime.combine(date, datetime.min.time().replace(hour=7, minute=0))
                        late_minutes = int((checkin_time - standard_time).total_seconds() / 60)
                    
                    Presensi.objects.create(
                        user=teacher,
                        tanggal=date,
                        jam_masuk=checkin_time.time(),
                        jam_pulang=checkout_time.time(),
                        status=status,
                        terlambat_menit=late_minutes,
                        jam_kerja_efektif=round(work_hours, 2),
                        lokasi_checkin='Sekolah',
                        lokasi_checkout='Sekolah'
                    )
                else:
                    # For izin, sakit, alpha - create with default times
                    Presensi.objects.create(
                        user=teacher,
                        tanggal=date,
                        jam_masuk=datetime.min.time().replace(hour=0, minute=0),  # Default time
                        status=status
                    )
        
        # Create sample leave applications
        leave_types = ['izin', 'sakit', 'cuti']
        leave_reasons = [
            'Keperluan keluarga yang tidak dapat ditinggalkan',
            'Sakit demam dan flu',
            'Cuti tahunan',
            'Urusan pribadi penting',
            'Sakit kepala dan mual'
        ]
        
        for teacher in teachers:
            # Create 1-3 leave applications per teacher
            for _ in range(random.randint(1, 3)):
                leave_type = random.choice(leave_types)
                start_date = today - timedelta(days=random.randint(1, 20))
                end_date = start_date + timedelta(days=random.randint(1, 3))
                
                # Random status
                status_choices = ['pending', 'pending', 'disetujui', 'ditolak']
                status = random.choice(status_choices)
                
                pengajuan = PengajuanIzin.objects.create(
                    user=teacher,
                    jenis_izin=leave_type,
                    tanggal_mulai=start_date,
                    tanggal_selesai=end_date,
                    keterangan=random.choice(leave_reasons),
                    status=status
                )
                
                # If approved/rejected, add approval info
                if status in ['disetujui', 'ditolak']:
                    pengajuan.tanggal_approval = timezone.now() - timedelta(days=random.randint(1, 5))
                    pengajuan.approved_by = AbstractUser.objects.filter(role='admin').first()
                    if status == 'ditolak':
                        pengajuan.alasan_penolakan = 'Jadwal tidak memungkinkan'
                    pengajuan.save()
        
        self.stdout.write(self.style.SUCCESS('Sample data generated successfully!'))
        self.stdout.write('Admin login: admin / admin123')
        self.stdout.write('Teacher login: GUR001 / guru123') 