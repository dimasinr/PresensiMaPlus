from django.shortcuts import redirect, render
from django.contrib.auth import logout as logout_auth
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db import models
from datetime import datetime, timedelta
from .models import AbstractUser, Presensi, PengajuanIzin, JamKerja
import json
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt

@login_required
def home(request):
    if request.user.is_authenticated:
        if request.user.abstract_user.role == 'admin':
            # Admin dashboard context
            today = timezone.now().date()
            
            # Get statistics for admin dashboard
            total_guru = AbstractUser.objects.filter(role='guru').count()
            hadir_hari_ini = Presensi.objects.filter(
                tanggal=today,
                status__in=['hadir', 'terlambat']
            ).count()
            terlambat_hari_ini = Presensi.objects.filter(
                tanggal=today,
                status='terlambat'
            ).count()
            pending_pengajuan = PengajuanIzin.objects.filter(status='pending').count()
            
            # Get recent presensi (check-in/check-out)
            recent_presensi = Presensi.objects.select_related('user').order_by('-tanggal', '-jam_masuk')[:5]
            # Get recent pengajuan izin
            recent_pengajuan = PengajuanIzin.objects.select_related('user').order_by('-tanggal_pengajuan')[:5]
            
            recent_activities = []
            for presensi in recent_presensi:
                recent_activities.append({
                    'user': presensi.user,
                    'action': f"Melakukan presensi pada {presensi.tanggal.strftime('%d/%m/%Y')}",
                    'timestamp': timezone.make_aware(timezone.datetime.combine(presensi.tanggal, presensi.jam_masuk))
                })
            
            for pengajuan in recent_pengajuan:
                recent_activities.append({
                    'user': pengajuan.user,
                    'action': f"Mengajukan {pengajuan.jenis_izin.title()} ({pengajuan.tanggal_mulai.strftime('%d/%m/%Y')})",
                    'timestamp': pengajuan.tanggal_pengajuan
                })
            
            # Sort by timestamp descending and take the latest 5
            recent_activities = sorted(recent_activities, key=lambda x: x['timestamp'], reverse=True)[:5]
            
            context = {
                'total_guru': total_guru,
                'hadir_hari_ini': hadir_hari_ini,
                'terlambat_hari_ini': terlambat_hari_ini,
                'pending_pengajuan': pending_pengajuan,
                'recent_activities': recent_activities,
                'recent_pengajuan': recent_pengajuan,
                'today': today,
            }
            
            return render(request, 'templates/home/admin/index.html', context)
        else:
            # Teacher dashboard context
            today = timezone.now().date()
            user = request.user.abstract_user
            
            # Get today's attendance
            today_presensi = Presensi.objects.filter(
                user=user,
                tanggal=today
            ).first()
            
            # Get monthly statistics
            current_month = timezone.now().month
            current_year = timezone.now().year
            
            monthly_presensi = Presensi.objects.filter(
                user=user,
                tanggal__month=current_month,
                tanggal__year=current_year
            )
            
            hadir_bulan_ini = monthly_presensi.filter(status='hadir').count()
            terlambat_bulan_ini = monthly_presensi.filter(status='terlambat').count()
            izin_bulan_ini = monthly_presensi.filter(status='izin').count()
            
            # Calculate average work hours
            avg_jam_kerja = monthly_presensi.aggregate(
                avg_hours=models.Avg('jam_kerja_efektif')
            )['avg_hours'] or 0
            
            # Get recent leave applications
            recent_pengajuan = PengajuanIzin.objects.filter(
                user=user
            ).order_by('-tanggal_pengajuan')[:5]
            
            context = {
                'today': today,
                'today_presensi': today_presensi,
                'hadir_bulan_ini': hadir_bulan_ini,
                'terlambat_bulan_ini': terlambat_bulan_ini,
                'izin_bulan_ini': izin_bulan_ini,
                'avg_jam_kerja': avg_jam_kerja,
                'recent_pengajuan': recent_pengajuan,
            }
            
            return render(request, 'templates/home/guru/index.html', context)
    else:
        return redirect('login')

def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        error_message = 'Invalid username or password'
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)  
            messages.success(request, 'Login Berhasil')
            return redirect('home') 
        else:
            messages.error(request, 'Username atau password salah')  
            return redirect('login') 
    return render(request, 'templates/auth/login.html')

def logout(request):
    logout_auth(request)
    return redirect('login')

# ADMIN TU
@login_required
def analisa_absensi(request):
    if request.user.abstract_user.role != 'admin':
        messages.error(request, 'Akses ditolak')
        return redirect('home')
    
    # Get month and year from GET parameters, default to current month
    selected_month = int(request.GET.get('month', timezone.now().month))
    selected_year = int(request.GET.get('year', timezone.now().year))
    
    # Validate month and year
    if selected_month < 1 or selected_month > 12:
        selected_month = timezone.now().month
    if selected_year < 2020 or selected_year > timezone.now().year + 1:
        selected_year = timezone.now().year
    
    # Get all teachers
    teachers = AbstractUser.objects.filter(role='guru')
    
    # Get attendance data for selected month
    attendance_data = []
    total_hadir = 0
    total_terlambat = 0
    total_izin = 0
    total_alpha = 0
    
    for teacher in teachers:
        presensi_list = Presensi.objects.filter(
            user=teacher,
            tanggal__month=selected_month,
            tanggal__year=selected_year
        ).order_by('tanggal')
        
        # Calculate statistics
        total_days = presensi_list.count()
        hadir = presensi_list.filter(status='hadir').count()
        terlambat = presensi_list.filter(status='terlambat').count()
        izin = presensi_list.filter(status='izin').count()
        sakit = presensi_list.filter(status='sakit').count()
        alpha = presensi_list.filter(status='alpha').count()
        
        # Add to totals
        total_hadir += hadir
        total_terlambat += terlambat
        total_izin += izin
        total_alpha += alpha
        
        # Calculate average work hours
        avg_work_hours = presensi_list.aggregate(
            avg_hours=models.Avg('jam_kerja_efektif')
        )['avg_hours'] or 0
        
        attendance_data.append({
            'teacher': teacher,
            'presensi_list': presensi_list,
            'total_days': total_days,
            'hadir': hadir,
            'terlambat': terlambat,
            'izin': izin,
            'sakit': sakit,
            'alpha': alpha,
            'avg_work_hours': round(avg_work_hours, 2),
            'attendance_rate': round((hadir + terlambat) / max(total_days, 1) * 100, 2)
        })
    
    # Create month options for filter
    month_options = []
    current_date = timezone.now()
    
    # Generate options for the last 12 months
    for i in range(12):
        date = current_date - timedelta(days=30*i)
        month_options.append({
            'value': date.month,
            'year': date.year,
            'label': date.strftime('%B %Y')
        })
    
    # Create formatted date for display
    selected_date = datetime(selected_year, selected_month, 1)
    formatted_date = selected_date.strftime('%B %Y')
    
    context = {
        'attendance_data': attendance_data,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'month_options': month_options,
        'formatted_date': formatted_date,
        'total_hadir': total_hadir,
        'total_terlambat': total_terlambat,
        'total_izin': total_izin,
        'total_alpha': total_alpha,
    }
    
    return render(request, 'templates/analisa_absensi.html', context)

@login_required
def daftar_guru(request):
    if request.user.abstract_user.role != 'admin':
        messages.error(request, 'Akses ditolak')
        return redirect('home')

    # Tambah Guru
    if request.method == 'POST':
        if 'add_guru' in request.POST:
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            nip = request.POST.get('nip')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            password = request.POST.get('password')
            if User.objects.filter(username=nip).exists():
                messages.error(request, 'NIP sudah terdaftar!')
            else:
                user = User.objects.create_user(username=nip, email=email, password=password)
                user.save()
                AbstractUser.objects.create(
                    user=user,
                    first_name=first_name,
                    last_name=last_name,
                    role='guru',
                    nip=nip,
                    phone=phone
                )
                messages.success(request, 'Guru berhasil ditambahkan!')
            return redirect('daftar_guru')
        elif 'delete_guru_id' in request.POST:
            guru_id = request.POST.get('delete_guru_id')
            try:
                guru = AbstractUser.objects.get(id=guru_id, role='guru')
                if guru.user:
                    guru.user.delete()
                guru.delete()
                messages.success(request, 'Guru berhasil dihapus!')
            except AbstractUser.DoesNotExist:
                messages.error(request, 'Guru tidak ditemukan!')
            return redirect('daftar_guru')

    teachers = AbstractUser.objects.filter(role='guru').order_by('first_name')
    # Get current month statistics for each teacher
    current_month = timezone.now().month
    current_year = timezone.now().year
    for teacher in teachers:
        monthly_presensi = Presensi.objects.filter(
            user=teacher,
            tanggal__month=current_month,
            tanggal__year=current_year
        )
        teacher.hadir_bulan_ini = monthly_presensi.filter(status='hadir').count()
        teacher.terlambat_bulan_ini = monthly_presensi.filter(status='terlambat').count()
        teacher.izin_bulan_ini = monthly_presensi.filter(status='izin').count()
        # Calculate attendance rate
        total_days = monthly_presensi.count()
        hadir_total = teacher.hadir_bulan_ini + teacher.terlambat_bulan_ini
        teacher.attendance_rate = round((hadir_total / max(total_days, 1)) * 100, 1)
    context = {
        'teachers': teachers
    }
    return render(request, 'templates/daftar_guru.html', context)

@login_required
def list_pengajuan(request):
    if request.user.abstract_user.role != 'admin':
        messages.error(request, 'Akses ditolak')
        return redirect('home')
    
    # Handle AJAX request for pengajuan detail
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        pengajuan_id = request.GET.get('pengajuan_id')
        try:
            pengajuan = PengajuanIzin.objects.get(id=pengajuan_id, user__role='guru')
            data = {
                'id': pengajuan.id,
                'guru_name': pengajuan.user.full_name,
                'guru_nip': pengajuan.user.nip or '-',
                'guru_phone': pengajuan.user.phone or '-',
                'jenis_izin': pengajuan.get_jenis_izin_display(),
                'tanggal_mulai': pengajuan.tanggal_mulai.strftime('%d/%m/%Y'),
                'tanggal_selesai': pengajuan.tanggal_selesai.strftime('%d/%m/%Y'),
                'keterangan': pengajuan.keterangan,
                'status': pengajuan.get_status_display(),
                'tanggal_pengajuan': pengajuan.tanggal_pengajuan.strftime('%d/%m/%Y %H:%M') if pengajuan.tanggal_pengajuan else '-',
                'tanggal_approval': pengajuan.tanggal_approval.strftime('%d/%m/%Y %H:%M') if pengajuan.tanggal_approval else '-',
                'approved_by': pengajuan.approved_by.full_name if pengajuan.approved_by else '-',
                'alasan_penolakan': pengajuan.alasan_penolakan or '-',
                'durasi_hari': (pengajuan.tanggal_selesai - pengajuan.tanggal_mulai).days + 1,
            }
            return JsonResponse({'success': True, 'data': data})
        except PengajuanIzin.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Pengajuan tidak ditemukan'})
    
    pengajuan_list = PengajuanIzin.objects.filter(
        user__role='guru'
    ).order_by('-tanggal_pengajuan')
    
    # Add duration calculation to each pengajuan
    for pengajuan in pengajuan_list:
        pengajuan.duration_days = (pengajuan.tanggal_selesai - pengajuan.tanggal_mulai).days + 1
    
    if request.method == 'POST':
        pengajuan_id = request.POST.get('pengajuan_id')
        action = request.POST.get('action')
        alasan = request.POST.get('alasan', '')
        
        try:
            pengajuan = PengajuanIzin.objects.get(id=pengajuan_id)
            
            if action == 'approve':
                pengajuan.status = 'disetujui'
                pengajuan.tanggal_approval = timezone.now()
                pengajuan.approved_by = request.user.abstract_user
                messages.success(request, 'Pengajuan berhasil disetujui')
            elif action == 'reject':
                pengajuan.status = 'ditolak'
                pengajuan.alasan_penolakan = alasan
                pengajuan.tanggal_approval = timezone.now()
                pengajuan.approved_by = request.user.abstract_user
                messages.success(request, 'Pengajuan berhasil ditolak')
            
            pengajuan.save()
            
        except PengajuanIzin.DoesNotExist:
            messages.error(request, 'Pengajuan tidak ditemukan')
    
    context = {
        'pengajuan_list': pengajuan_list
    }
    
    return render(request, 'templates/list_pengajuan.html', context)

# GURU
@login_required
def absensi(request):
    if request.user.abstract_user.role != 'guru':
        messages.error(request, 'Akses ditolak')
        return redirect('home')
    
    today = timezone.now().date()
    user = request.user.abstract_user
    
    # Check if already checked in today
    today_presensi = Presensi.objects.filter(
        user=user,
        tanggal=today
    ).first()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'checkin':
            if not today_presensi:
                # Create new attendance record
                presensi = Presensi.objects.create(
                    user=user,
                    tanggal=today,
                    jam_masuk=timezone.now().time(),
                    image_checkin=request.FILES.get('image_checkin'),
                    lokasi_checkin=request.POST.get('lokasi', '')
                )
                messages.success(request, 'Check-in berhasil')
            else:
                messages.warning(request, 'Anda sudah melakukan check-in hari ini')
        
        elif action == 'checkout':
            if today_presensi and not today_presensi.jam_pulang:
                today_presensi.jam_pulang = timezone.now().time()
                today_presensi.image_checkout = request.FILES.get('image_checkout')
                today_presensi.lokasi_checkout = request.POST.get('lokasi', '')
                today_presensi.save()
                messages.success(request, 'Check-out berhasil')
            else:
                messages.warning(request, 'Anda belum check-in atau sudah check-out')
    
    context = {
        'today_presensi': today_presensi,
        'today': today
    }
    
    return render(request, 'templates/absensi.html', context)

@login_required
def history_absensi(request):
    if request.user.abstract_user.role != 'guru':
        messages.error(request, 'Akses ditolak')
        return redirect('home')
    
    user = request.user.abstract_user

    # Get month filter
    try:
        month = int(request.GET.get('month', ''))
    except (TypeError, ValueError):
        month = timezone.now().month
    if not (1 <= month <= 12):
        month = timezone.now().month
    try:
        year = int(request.GET.get('year', ''))
    except (TypeError, ValueError):
        year = timezone.now().year
    if not (2000 <= year <= 2100):
        year = timezone.now().year

    presensi_list = Presensi.objects.filter(
        user=user,
        tanggal__month=month,
        tanggal__year=year
    ).order_by('-tanggal')
    
    # Calculate monthly statistics
    total_days = presensi_list.count()
    hadir = presensi_list.filter(status='hadir').count()
    terlambat = presensi_list.filter(status='terlambat').count()
    izin = presensi_list.filter(status='izin').count()
    sakit = presensi_list.filter(status='sakit').count()
    alpha = presensi_list.filter(status='alpha').count()
    
    now_year = timezone.now().year
    tahun_range = list(range(now_year-5, now_year+3))

    context = {
        'presensi_list': presensi_list,
        'total_days': total_days,
        'months': range(1,13),
        'hadir': hadir,
        'terlambat': terlambat,
        'izin': izin,
        'sakit': sakit,
        'alpha': alpha,
        'selected_month': month,
        'selected_year': year,
        'tahun_range': tahun_range,
    }
    
    return render(request, 'templates/history_absensi.html', context)

@login_required
def pengajuan(request):
    if request.user.abstract_user.role != 'guru':
        messages.error(request, 'Akses ditolak')
        return redirect('home')
    
    user = request.user.abstract_user
    
    if request.method == 'POST':
        if 'add_pengajuan' in request.POST:
            jenis_izin = request.POST.get('jenis_izin')
            tanggal_mulai = request.POST.get('tanggal_mulai')
            tanggal_selesai = request.POST.get('tanggal_selesai')
            keterangan = request.POST.get('keterangan')
            
            # Validate dates
            try:
                start_date = datetime.strptime(tanggal_mulai, '%Y-%m-%d').date()
                end_date = datetime.strptime(tanggal_selesai, '%Y-%m-%d').date()
                
                if start_date > end_date:
                    messages.error(request, 'Tanggal selesai harus setelah tanggal mulai')
                elif start_date < timezone.now().date():
                    messages.error(request, 'Tanggal mulai tidak boleh di masa lalu')
                else:
                    # Create leave application
                    PengajuanIzin.objects.create(
                        user=user,
                        jenis_izin=jenis_izin,
                        tanggal_mulai=start_date,
                        tanggal_selesai=end_date,
                        keterangan=keterangan
                    )
                    messages.success(request, 'Pengajuan izin berhasil dikirim')
                    return redirect('pengajuan')
                    
            except ValueError:
                messages.error(request, 'Format tanggal tidak valid')
        
        elif 'delete_pengajuan_id' in request.POST:
            pengajuan_id = request.POST.get('delete_pengajuan_id')
            try:
                pengajuan = PengajuanIzin.objects.get(id=pengajuan_id, user=user)
                if pengajuan.status == 'pending':
                    pengajuan.delete()
                    messages.success(request, 'Pengajuan berhasil dihapus')
                else:
                    messages.error(request, 'Hanya pengajuan pending yang dapat dihapus')
            except PengajuanIzin.DoesNotExist:
                messages.error(request, 'Pengajuan tidak ditemukan')
            return redirect('pengajuan')
    
    # Get user's leave applications
    pengajuan_list = PengajuanIzin.objects.filter(
        user=user
    ).order_by('-tanggal_pengajuan')
    
    # Add duration calculation to each pengajuan
    for pengajuan in pengajuan_list:
        pengajuan.duration_days = (pengajuan.tanggal_selesai - pengajuan.tanggal_mulai).days + 1
    
    context = {
        'pengajuan_list': pengajuan_list
    }
    
    return render(request, 'templates/pengajuan.html', context)

@login_required
def ubah_password_guru(request):
    if request.user.abstract_user.role != 'admin':
        return JsonResponse({'success': False, 'error': 'Akses ditolak'}, status=403)
    if request.method == 'POST':
        guru_id = request.POST.get('guru_id')
        new_password = request.POST.get('new_password')
        if not guru_id or not new_password:
            return JsonResponse({'success': False, 'error': 'Data tidak lengkap'}, status=400)
        try:
            guru = AbstractUser.objects.get(id=guru_id, role='guru')
            user = guru.user
            user.set_password(new_password)
            user.save()
            return JsonResponse({'success': True, 'message': 'Password berhasil diubah'})
        except AbstractUser.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Guru tidak ditemukan'}, status=404)
    return JsonResponse({'success': False, 'error': 'Metode tidak diizinkan'}, status=405)