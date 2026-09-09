import streamlit as st
import pandas as pd
from supabase import create_client, Client
import io

# 1. KONFIGURASI DAN STYLING PREMIUM
st.set_page_config(page_title="Sistem Kelompok Kelas Real-Time", layout="wide", page_icon="👥")

st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    h1 { color: #1E3A8A; font-weight: 800; text-align: center; }
    .stButton>button { width: 100%; border-radius: 6px; font-weight: 600; }
    .status-penuh { color: #DC2626; font-weight: bold; background-color: #FEE2E2; padding: 2px 8px; border-radius: 4px; }
    .status-tersedia { color: #16A34A; font-weight: bold; background-color: #DCFCE7; padding: 2px 8px; border-radius: 4px; }
    .card-kelompok { background-color: #FFFFFF; border: 1px solid #E5E7EB; padding: 15px; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
    </style>""", unsafe_allow_html=True)

# 2. KONEKSI DATABASE SUPABASE SECARA AMAN
# Mengambil kredensial dari Streamlit Secrets (Akan kita setting di Langkah 5)
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_supabase()

# --- FUNGSI-FUNGSI ENGINE DATABASE (CRUD CORES) ---
def ambil_semua_kelas():
    res = supabase.table("master_kelas").select("nama_kelas").order("nama_kelas").execute()
    return [item["nama_kelas"] for item in res.data]

def ambil_detail_kelas(nama_kelas):
    res = supabase.table("master_kelas").select("*").eq("nama_kelas", nama_kelas).execute()
    return res.data[0] if res.data else None

def ambil_kelompok_kelas(nama_kelas):
    res = supabase.table("data_kelompok").select("*").eq("nama_kelas", nama_kelas).order("kelompok_id").execute()
    return res.data

def ambil_anggota_kelas(nama_kelas):
    res = supabase.table("anggota_kelas").select("*").eq("nama_kelas", nama_kelas).execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=["nama_mahasiswa", "npm_mahasiswa", "nama_kelompok"])

# --- TAMPILAN UTAMA INTERAKTIF ---
st.title("👥 Sistem Pemilihan Kelompok Kelas Universal")
st.markdown("<p style='text-align: center; color: #4B5563;'>Sistem pembagian slot kelompok terintegrasi cloud, anti-bentrok, dan real-time untuk seluruh program studi.</p>", unsafe_allow_html=True)
st.divider()

# PILIHAN RUANG KELAS UTAMA UNTUK MAHASISWA DAN PJ
list_kelas = ambil_semua_kelas()
col_header1, col_header2 = st.columns([2, 1])
with col_header1:
    pilihan_kelas = st.selectbox("📖 Pilih Ruang Kelas / Mata Kuliah Anda:", ["-- Pilih Kelas --"] + list_kelas)

# --- ALUR UTAMA JIKA KELAS SUDAH DIPILIH ---
if pilihan_kelas != "-- Pilih Kelas --":
    detail_kelas = ambil_detail_kelas(pilihan_kelas)
    list_kelompok = ambil_kelompok_kelas(pilihan_kelas)
    df_anggota = ambil_anggota_kelas(pilihan_kelas)
    
    # RENDER HEADER SPESIFIK KELOMPOK
    st.subheader(f"📌 {detail_kelas['nama_kelas']}")
    st.info(f"💬 Petunjuk PJ: {detail_kelas['deskripsi']}")
    
    # SIDEBAR KHUSUS PENDAFTARAN MAHASISWA (SANGAT KETAT)
    st.sidebar.header("👤 Form Pendaftaran")
    if detail_kelas["dikunci"]:
        st.sidebar.error("🔒 Pendaftaran kelompok untuk kelas ini telah DIKUNCI oleh PJ.")
        input_nama, input_npm = "", ""
    else:
        input_nama = st.sidebar.text_input("Masukkan Nama Lengkap:").strip()
        input_npm = st.sidebar.text_input("Masukkan NPM / NIM:").strip()
        
        # Validasi Keketatan Data Mahasiswa (Anti-Ganda/Anti-Curang)
        sudah_daftar = not df_anggota[df_anggota["npm_mahasiswa"] == input_npm].empty if input_npm else False
        
        if input_nama and input_npm:
            if sudah_daftar:
                mhs_row = df_anggota[df_anggota["npm_mahasiswa"] == input_npm].iloc[0]
                st.sidebar.warning(f"NPM {input_npm} sudah mengambil slot di **{mhs_row['nama_kelompok']}**.")
                
                if st.sidebar.button("❌ Batalkan Slot Saya", type="secondary"):
                    supabase.table("anggota_kelas").delete().eq("nama_kelas", pilihan_kelas).eq("npm_mahasiswa", input_npm).execute()
                    st.sidebar.success("Slot Anda berhasil dibatalkan!")
                    st.rerun()
            else:
                st.sidebar.info("🟢 Identitas aman. Silakan klik tombol 'Ambil Slot' di kanan.")

    # --- PAPAN VISUAL GRID RESPONSIVE (MAHASISWA ONLY SCREEN) ---
    st.write("### 📋 Papan Ketersediaan Slot Kelompok")
    cols = st.columns(3)
    
    for idx, kel in enumerate(list_kelompok):
        col = cols[idx % 3]
        m_terdaftar = df_anggota[df_anggota["nama_kelompok"] == kel["nama_kelompok"]]
        terisi = len(m_terdaftar)
        kapasitas = kel["kapasitas"]
        
        with col:
            st.markdown(f"""
            <div class='card-kelompok'>
                <h3 style='margin-bottom:5px; color:#1E3A8A;'>👥 {kel['nama_kelompok']}</h3>
            </div>
            """, unsafe_allow_html=True)
            
            # Progress Bar Status Keterisian
            st.progress(min(terisi / kapasitas, 1.0))
            if terisi >= kapasitas:
                st.markdown(f"Status: <span class='status-penuh'>{terisi} / {kapasitas} (Penuh)</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"Status: <span class='status-tersedia'>{terisi} / {kapasitas} Tersedia</span>", unsafe_allow_html=True)
            
            st.write("")
            # Render list nama di dalam slot
            for i in range(kapasitas):
                if i < terisi:
                    row_mhs = m_terdaftar.iloc[i]
                    st.error(f"🔴 **Slot {i+1}:** {row_mhs['nama_mahasiswa']} ({row_mhs['npm_mahasiswa']})")
                else:
                    st.success(f"🟢 **Slot {i+1}:** [ KOSONG ]")
            
            # Tombol Eksekusi Instan untuk Mahasiswa
            if not detail_kelas["dikunci"] and input_nama and input_npm and not sudah_daftar:
                if terisi < kapasitas:
                    if st.button(f"Ambil Slot {kel['nama_kelompok']}", key=f"join_{kel['kelompok_id']}", type="primary"):
                        supabase.table("anggota_kelas").insert({
                            "nama_kelas": pilihan_kelas,
                            "nama_mahasiswa": input_nama,
                            "npm_mahasiswa": input_npm,
                            "nama_kelompok": kel["nama_kelompok"]
                        }).execute()
                        st.rerun()
            st.write("---")

    # --- FITUR DOWNLOAD REKAP OTOMATIS FILTER FILTER PER KELOMPOK ---
    st.write("### 📥 Unduh Berkas Rekap Kelas")
    if not df_anggota.empty:
        # Otomatis mensortir rapi per kelompok dan nama mahasiswa
        df_rapi = df_anggota.sort_values(by=["nama_kelompok", "nama_mahasiswa"]).reset_index(drop=True)
        df_export = df_rapi[["nama_kelompok", "nama_mahasiswa", "npm_mahasiswa"]].rename(
            columns={"nama_kelompok": "Kelompok", "nama_mahasiswa": "Nama Lengkap Mahasiswa", "npm_mahasiswa": "NPM / NIM"}
        )
        
        st.dataframe(df_export, use_container_width=True)
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_export.to_excel(writer, index=False, sheet_name='Rekap Hasil Kelompok')
        
        st.download_button(
            label="🟢 Download File Excel Kelas (.xlsx)",
            data=buffer.getvalue(),
            file_name=f"REKAP_KELOMPOK_{pilihan_kelas.replace(' ', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("Belum ada mahasiswa yang mengambil slot kelompok di kelas ini.")

    # --- PANEL KONTROL KHUSUS PJ (TERKUNCI PIN TEGAS) ---
    st.write("##")
    with st.expander("🔑 Panel Manajemen Kontrol PJ Kelas (Butuh PIN Auth)"):
        input_pin = st.text_input("Masukkan PIN Admin Kelas Ini:", type="password", key=f"pin_{pilihan_kelas}")
        if input_pin == detail_kelas["pin_admin"]:
            st.success("🔓 Hak Akses PJ Terverifikasi! Anda diizinkan merubah pengaturan.")
            
            edit_desk = st.text_area("Ubah Deskripsi Petunjuk:", value=detail_kelas["deskripsi"])
            toggle_kunci = st.toggle("🔒 Kunci Akses Pengisian Mahasiswa (Lock All)", value=detail_kelas["dikunci"])
            
            if st.button("💾 Simpan Perubahan Setelan Kelas"):
                supabase.table("master_kelas").update({"deskripsi": edit_desk, "dikunci": toggle_kunci}).eq("nama_kelas", pilihan_kelas).execute()
                st.success("Setelan kelas diperbarui!")
                st.rerun()
                
            st.divider()
            st.write("**⚠️ Menu Bahaya Kontrol Sesi:**")
            if st.button("🔴 RESET & HAPUS TOTAL RUANG KELAS INI"):
                supabase.table("master_kelas").delete().eq("nama_kelas", pilihan_kelas).execute()
                st.success("Ruang kelas sukses dihapus dari database pusat!")
                st.rerun()
        elif input_pin != "":
            st.error("PIN Salah! Mahasiswa dilarang mengotak-atik panel ini.")

# --- ALUR JIKA PJ INGIN MEMBUAT RUANG BARU SECARA REAL-TIME ---
st.divider()
with st.expander("➕ PJ Baru? Klik di Sini untuk Membuat Ruang Pembagian Kelompok Baru"):
    st.write("Buat ruang pendaftaran terpisah khusus untuk kelas atau mata kuliah Anda sendiri:")
    new_nama_kelas = st.text_input("Nama Mata Kuliah & Kelas:", placeholder="Contoh: Basis Data Kelas R4D")
    new_deskripsi = st.text_area("Deskripsi / Aturan Kelompok:", value="Pilih slot kelompokmu yang masih tersedia. Ingat, satu mahasiswa hanya bisa memilih 1 slot!")
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        new_j_kel = st.number_input("Jumlah Kelompok yang Ingin Dibuat:", min_value=1, max_value=40, value=5)
    with col_c2:
        new_kap = st.number_input("Kapasitas Batas Anggota per Kelompok:", min_value=1, max_value=100, value=4)
        
    new_pin = st.text_input("Buat PIN Keamanan Admin Ruang Ini:", type="password", help="PIN ini wajib Anda simpan untuk mengontrol kelas ini ke depannya.")
    
    if st.button("🚀 Buat dan Aktifkan Ruang Kelas", type="primary"):
        if new_nama_kelas and new_pin:
            try:
                # 1. Daftarkan kelas ke database pusat
                supabase.table("master_kelas").insert({
                    "nama_kelas": new_nama_kelas,
                    "deskripsi": new_deskripsi,
                    "pin_admin": new_pin,
                    "jumlah_kelompok": int(new_j_kel),
                    "kapasitas_per_kelompok": int(new_kap)
                }).execute()
                
                # 2. Generate baris kelompok secara otomatis ke database kelompok
                for num in range(1, int(new_j_kel) + 1):
                    supabase.table("data_kelompok").insert({
                        "nama_kelas": new_nama_kelas,
                        "nama_kelompok": f"Kelompok {num}",
                        "kapasitas": int(new_kap)
                    }).execute()
                    
                st.success(f"Berhasil membuat ruang kelas '{new_nama_kelas}'! Silakan pilih nama kelas Anda pada menu dropdown di atas.")
                st.rerun()
            except Exception as e:
                st.error("Nama kelas sudah terdaftar! Gunakan nama yang lebih spesifik (misal tambah nama prodi/tahun).")
        else:
            st.error("Nama Kelas dan PIN Admin wajib diisi!")
