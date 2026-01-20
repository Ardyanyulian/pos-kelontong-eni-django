import os
import json
import time
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator
from datetime import datetime
from django.db.models import Sum, FloatField
from django.db.models.functions import TruncDate, Cast
from django.contrib import messages

# Import Class 
from .logic.Barang import Barang as BarangClass
from .logic.Admin import Admin as AdminClass
from .logic.Assistant import Assistant as AssistantClass
from .logic.Transaksi import Transaksi as TransaksiClass
from .logic.Detail_Transaksi import Detail_Transaksi as DetailTransaksiClass

# Import Model DB & Algoritma
from .models import Barang as BarangModel
from .models import Pegawai as PegawaiModel
from .models import Transaksi as TransaksiModel
from .models import DetailTransaksi as DetailModel

from .logic.Algorithms import quicksort

# menu_display/views.py
def tampilkan_menu(request):

    DATA_MENU = [
        {"id": 1, "nama": "Nasi Ayam Pop", "harga": 22000, "tersedia": True},
        {"id": 2, "nama": "Gulai Kepala Ikan Kakap", "harga": 35000, "tersedia": True},
        {"id": 3, "nama": "Telur Dadar Sayur", "harga": 10000, "tersedia": True},
        {"id": 4, "nama": "Es Teh Manis", "harga": 6000, "tersedia": False}, 
    ]

    context = {
        'judul_halaman': "Daftar Menu Khas Padang",
        'daftar_item': DATA_MENU,
        'nama_warung': "Warung Makan Berkah",
    }
    
    return render(request, 'menu_display/menu.html', context)


def tampilkan_index(request):
    pembeli1 = AbstractClass.pembeli("Iyan", 200)
    context = {
        'pembeli': pembeli1,
        'pler': "Makado"
    }
    
    return render(request, 'menu_display/index.html', context)


def tampilkan_about(request):
    nama = request.session.get('username')
    password = request.session.get('password')
    
    if not nama:
        return redirect('login')
    
    return render(request, 'about/about.html')


def tampilkan_dashboard(request):
    nama = request.session.get('username')
    if not nama:
        return redirect('login')
    
    barangMentah = BarangModel.objects.all()
    daftarBarang = []
    total_aset_warung = 0
    jumlah_stok_rendah = 0

    for barang in barangMentah:
        barangOOP = BarangClass(
            barang.id,
            barang.nama,
            barang.stok,
            barang.hargabeli,
            barang.hargajual
        )
        total_aset_warung += (int(barang.stok) * int(barang.hargajual))
        if barang.stok < 10:
            jumlah_stok_rendah += 1
        daftarBarang.append(barangOOP)
     
    context = {
        'daftarBarang': daftarBarang,
        'total_aset': total_aset_warung,
        'stok_rendah_count': jumlah_stok_rendah,
        'username': nama,
        'hak': request.session.get('hak')
    }
    return render(request, 'menu_display/dashboard.html', context)

#================================LOGIKA LOGIN=====================================
def tampilkan_login(request):
    if request.session.get('username'):
        return redirect('dashboard')

    if request.method == 'POST':
        username_input = request.POST.get('nama')
        password_input = request.POST.get('password')

        pegawai_db = PegawaiModel.objects.filter(nama=username_input, password=password_input).first()
        
        if pegawai_db:
            role = pegawai_db.id_status.nama_status.lower() 
            if role == 'admin':
                user_obj = AdminClass(pegawai_db.nama, pegawai_db.password, pegawai_db.nomor_telepon)
            else:
                user_obj = AssistantClass(pegawai_db.nama, pegawai_db.password, pegawai_db.nomor_telepon)

            request.session['ID'] = pegawai_db.id_pegawai
            request.session['username'] = user_obj.getNama()
            request.session['hak'] = role
            request.session['nomorHp'] = user_obj.getNomorTelepon()
            request.session['foto'] = pegawai_db.foto_profil
            return redirect('dashboard')
            
    return render(request, 'menu_display/login.html')

#================================LOGIKA PROFILE===============================
def tampilkan_profile(request, ID):
    if not request.session.get('username'):
        return redirect('login')
    
    pegawai = PegawaiModel.objects.get(id_pegawai=ID)
    context = {'ID': ID, 'pegawai': pegawai}
    return render(request, 'menu_display/profile.html', context)

def tampilkan_logout(request):
    request.session.clear()
    return redirect('login')

def update_profile(request, ID):
    if request.method == 'POST':
        p_db = PegawaiModel.objects.get(id_pegawai=ID)
        role = request.session.get('hak')

        if role == 'admin':
            user_obj = AdminClass(p_db.nama, p_db.password, p_db.nomor_telepon)
        else:
            user_obj = AssistantClass(p_db.nama, p_db.password, p_db.nomor_telepon)

        user_obj.setNama(request.POST.get('nama'))
        user_obj.setNomorTelepon(request.POST.get('nomorHp'))
        
        p_db.nama = user_obj.getNama()
        p_db.nomor_telepon = user_obj.getNomorTelepon()
        p_db.save()
        
        request.session['username'] = p_db.nama
        return redirect('profile', ID=ID)

def upload_foto_saja(request, ID):
    if request.method == 'POST' and request.FILES.get('foto_input'):
        try:
            foto = request.FILES.get('foto_input')
            
            target_dir = os.path.join(settings.MEDIA_ROOT, 'pegawai')
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)

            fs = FileSystemStorage()
            import time
            ext = os.path.splitext(foto.name)[1]
            filename = fs.save(f"pegawai/{ID}_{int(time.time())}{ext}", foto)
            file_url = fs.url(filename)

            pegawai = PegawaiModel.objects.get(id_pegawai=ID)
            pegawai.foto_profil = file_url
            pegawai.save()

            request.session['foto'] = file_url
            return JsonResponse({'success': True, 'url': file_url})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)



#==================================LOGIKA BARANG============================
def tampilkan_gudang(request):
    nama = request.session.get('username')
    if not nama:
        return redirect('login')
    
    query_db = BarangModel.objects.all()
    
    daftar_objek_oop = []
    for b in query_db:
        objek = BarangClass(
            ID=b.id, 
            nama=b.nama, 
            stok=b.stok, 
            hargaBeli=b.hargabeli, 
            hargaJual=b.hargajual
        )
        daftar_objek_oop.append(objek)

    barang_terurut = quicksort(daftar_objek_oop)

    for items in barang_terurut:
        items.total = int(items.stok) * int(items.hargaJual)
    
    p = Paginator(barang_terurut, 5)
    nomor_halaman = request.GET.get('page')
    objek_halaman = p.get_page(nomor_halaman)
    
    context = {
        'barang': objek_halaman
    }
    
    return render(request, 'menu_display/gudang.html', context)

def hapus_barang(request, id_barang):
    b_db = BarangModel.objects.get(id=id_barang)
    objek = BarangClass(b_db.id, b_db.nama, b_db.stok, b_db.hargabeli, b_db.hargajual)
    target_id = objek.hapusBarang()
    BarangModel.objects.filter(id=target_id).delete()
    return redirect('gudang')


def tambah_barang(request):
    if request.method == "POST":
        id_input = request.POST.get('id')
        nama_input = request.POST.get('nama')
        stok_input = request.POST.get('stok')
        beli_input = request.POST.get('hargaBeli')
        jual_input = request.POST.get('hargaJual')

        BarangModel.objects.create(
            id=id_input,
            nama=nama_input,
            stok=int(stok_input),
            hargabeli=float(beli_input),
            hargajual=float(jual_input)
        )
        return redirect('gudang')
    
    return redirect('tambah-barang')

def tambahStok(request):
    if request.method == "POST":
        id_barang = request.POST.get('id_barang')
        jumlah = int(request.POST.get('jumlah', 0))
        
        b_db = BarangModel.objects.filter(id=id_barang).first()
        
        if b_db:
            objek = BarangClass(b_db.id, b_db.nama, b_db.stok, b_db.hargabeli, b_db.hargajual)
            objek.tambahStok(jumlah)
            
            b_db.stok = objek.infoStok()
            b_db.save()
            
    return redirect('gudang')

def kurangiStok(request):
    if request.method == "POST":
        id_barang = request.POST.get('id_barang')
        jumlah = int(request.POST.get('jumlah', 0))
        
        b_db = BarangModel.objects.get(id=id_barang)
        objek = BarangClass(b_db.id, b_db.nama, b_db.stok, b_db.hargabeli, b_db.hargajual)
        
        objek.kurangiStok(jumlah)
        
        b_db.stok = objek.infoStok()
        b_db.save()
    return redirect('gudang')

def tampilkan_form_barang(request):
    nama = request.session.get('username')
    
    if not nama:
        return redirect('login')
    
    return render(request, 'menu_display/tambah.html' )



#====================================LOGIKA TRANSAKSI===========================

def tampilkan_transaksi(request):
    nama = request.session.get('username')
    if not nama: return redirect('login')
    
    tahun_saiki = datetime.now().strftime("%Y")
    last_trx = TransaksiModel.objects.order_by('-id_transaksi').first()
    new_id_num = (last_trx.id_transaksi + 1) if last_trx else 1
    
    context = {
        'next_id': f"TRX-{tahun_saiki}{str(new_id_num).zfill(3)}",
        'daftar_barang': BarangModel.objects.all()
    }
    return render(request, 'menu_display/transaksi.html', context)

def tambah_transaksi(request):
    if request.method == "POST":
        # Ambil tanggal dari form agar tidak otomatis tanggal 19
        tanggal_input = request.POST.get('tanggal_transaksi')
        
        # Inisialisasi wrapper
        wrapper_trx = TransaksiClass(namaPembeli=request.POST.get('nama_pembeli'))
        
        barang_ids = request.POST.getlist('item_barang[]')
        qtys = request.POST.getlist('item_qty[]')

        if not barang_ids or sum(int(q) for q in qtys if q) <= 0:
            return redirect('transaksi') # Atau kirim pesan error

        total_kalkulasi_manual = 0 # Cadangan perhitungan manual

        for b_id, qty in zip(barang_ids, qtys):
            if not b_id or not qty: continue
            
            b_db = BarangModel.objects.get(id=b_id)
            
            # Buat objek barang OOP
            wrap_barang = BarangClass(
                ID=b_db.id, 
                nama=b_db.nama, 
                stok=b_db.stok, 
                hargaBeli=b_db.hargabeli, 
                hargaJual=b_db.hargajual
            )
            
            # Masukkan ke detail pesanan
            wrap_detail = DetailTransaksiClass(barang_obj=wrap_barang, kuantitas=int(qty))
            wrapper_trx.Pesanan(wrap_detail)
            
            # Hitung total manual untuk memastikan data tidak 0
            total_kalkulasi_manual += (float(b_db.hargajual) * int(qty))

            # Kurangi stok di DB
            b_db.stok -= int(qty)
            b_db.save()

        # Simpan ke TransaksiModel
        # Gunakan total_kalkulasi_manual jika getTotalBayar() tetap 0
        final_total = wrapper_trx.getTotalBayar()
        if final_total == 0 or final_total is None:
            final_total = total_kalkulasi_manual

        new_trx_db = TransaksiModel.objects.create(
            nama_pembeli=wrapper_trx.namaPembeli,
            tanggal=tanggal_input if tanggal_input else datetime.now().date(),
            total_harga=final_total, # Simpan nilai total di sini
            id_pegawai_id=request.session.get('ID')
        )

        # Simpan Detail ke DB
        for d in wrapper_trx.detailPesanan:
            DetailModel.objects.create(
                id_transaksi=new_trx_db,
                id_barang_id=d.getBarang().ID,
                jumlah=d.getKuantitas(),
                harga_satuan=d.getBarang().hargaJual, 
                subtotal_harga=d.getSubTotal() 
            )

        return redirect('dashboard')


def tampilkan_detail_transaksi(request, id_transaksi):
    nama = request.session.get('username')
    
    if not nama:
        return redirect('login')
    
    transaksi_db = TransaksiModel.objects.get(id_transaksi=id_transaksi)
    
    context = {
        'transaksi': transaksi_db
    }
    
    return render(request, 'menu_display/laporan.html', context)

def hapus_detail_transaksi(request, id_transaksi):
    pass

#=============================================================================


#====================================LOGIKA LAPORAN===========================

def tampilkan_laporan(request):
    nama = request.session.get('username')
    if not nama:
        return redirect('login')

    barang_mentah = BarangModel.objects.all()
    total_pendapatan = 0
    for b in barang_mentah:
        total_pendapatan += (b.hargajual * b.stok)

    
    transaksi_qs = TransaksiModel.objects.all()
    banyak_transaksi = 0
    for t in transaksi_qs:
        banyak_transaksi += 1

    
    laba_bersih = 0
    details = DetailModel.objects.filter(id_transaksi__in=transaksi_qs).select_related('id_barang')
    
    for d in details:
        margin = d.harga_satuan - d.id_barang.hargabeli
        laba_bersih += (margin * d.jumlah)


    stok_menipis_count = 0
    for b in barang_mentah:
        if b.stok <= 10:
            stok_menipis_count += 1

    
    tgl_mulai = request.GET.get('tgl_mulai')
    tgl_akhir = request.GET.get('tgl_akhir')

    if tgl_mulai and tgl_akhir:
        transaksi_qs = transaksi_qs.filter(tanggal__range=[tgl_mulai, tgl_akhir])
    
    transaksi_qs = transaksi_qs.order_by('-id_transaksi')

    total_pendapatan = 0
    for t in transaksi_qs:
        total_pendapatan += t.total_harga

    total_transaksi_count = transaksi_qs.count()

    paginator = Paginator(transaksi_qs, 5) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'total_pendapatan': total_pendapatan,
        'total_transaksi': total_transaksi_count,
        'page_obj': page_obj,
        'stok_menipis': stok_menipis_count,
        'laba_bersih': laba_bersih,
        'tgl_mulai': tgl_mulai,
        'tgl_akhir': tgl_akhir,
    }
    
    return render(request, 'menu_display/laporan.html', context)


#=============================================================================

def tampilkan_settings(request):
    nama = request.session.get('username')
    
    if not nama:
        return redirect('login')
    
    return render(request, 'menu_display/settings.html')

def tampilkan_staff(request):
    nama = request.session.get('username')
    
    if not nama:
        return redirect('login')
    
    return render(request, 'menu_display/staff.html')

def tampilkan_manage(request):
    nama = request.session.get('username')
    
    if not nama:
        return redirect('login')
    
    return render(request, 'menu_display/manage.html' )