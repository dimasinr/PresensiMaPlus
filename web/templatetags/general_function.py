from django import template
import locale
import datetime

register = template.Library()

@register.filter
def format_rupiah(amount):
    locale.setlocale(locale.LC_ALL, 'id_ID.UTF-8')
    return locale.currency(amount, symbol='Rp', grouping=True)

@register.filter
def format_angka(angka):
    return "{:,.0f}".format(angka)

@register.filter
def convert_date(tanggal_str):
    if isinstance(tanggal_str, str):
        tanggal = datetime.datetime.strptime(tanggal_str, "%b. %d, %Y, %I:%M %p")
    else:
        tanggal = tanggal_str
    
    # Dictionary untuk nama hari dan bulan dalam bahasa Indonesia
    hari_dict = {0: "SENIN", 1: "SELASA", 2: "RABU", 3: "KAMIS", 4: "JUMAT", 5: "SABTU", 6: "MINGGU"}
    bulan_dict = {1: "JAN", 2: "FEB", 3: "MAR", 4: "APR", 5: "MEI", 6: "JUN", 7: "JUL", 8: "AGU", 9: "SEP", 10: "OKT", 11: "NOV", 12: "DES"}
    
    # Mendapatkan hari dalam huruf, tanggal, bulan, dan tahun
    hari = hari_dict[tanggal.weekday()]
    tanggal_hari = tanggal.day
    bulan = bulan_dict[tanggal.month]
    tahun = tanggal.year
    
    # Mengembalikan format yang diinginkan
    return f"{hari}\t{tanggal_hari}\t{bulan}\t{tahun}"

@register.filter
def get_bulan_id(bulan):
    bulan_dict = {
        1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April', 5: 'Mei', 6: 'Juni',
        7: 'Juli', 8: 'Agustus', 9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
    }
    try:
        return bulan_dict[int(bulan)]
    except (KeyError, ValueError, TypeError):
        return bulan