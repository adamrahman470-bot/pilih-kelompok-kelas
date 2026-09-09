import streamlit as st
import pandas as pd
from supabase import create_client, Client
import io
import time

# 1. KONFIGURASI DAN STYLING PREMIUM
st.set_page_config(page_title="Sistem Kelompok Kelas Real-Time", layout="wide", page_icon="👥")

st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    h1 { color: #1E3A8A; font-weight: 800; text-align: center; margin-bottom: 0.2rem; }
    .stButton>button { width: 100%; border-radius: 6px; font-weight: 600; }
    .status-penuh { color: #DC2626; font-weight: bold; background-color: #FEE2E2; padding: 2px 8px; border-radius: 4px; }
    .status-tersedia { color: #16A34A; font-weight: bold; background-color: #DCFCE7; padding: 2px 8px; border-radius: 4px; }
    .card-kelompok { background-color: #FFFFFF; border: 1px solid #E5E7EB; padding: 15px; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
    
    .dev-badge {
        display: inline-block;
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
        color: #FFFFFF !important;
        padding: 5px 18px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        box-shadow: 0 4px 10px rgba(30, 58, 138, 0.25);
        margin-top: 8px;
    }
    </style>""", unsafe_allow_html=True)

# 2. KONEKSI DATABASE SUPABASE SECARA AMAN
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_supabase()

# --- FUNGSI ENGINE DATABASE ---
def ambil_semua_kelas():
    try:
        res = supabase.table("master_kelas").select("nama_kelas").order("nama_kelas").execute()
        return [item["nama_kelas"] for item in res.data]
    except Exception:
        return []

def ambil_detail_kelas(nama_kelas):
    res = supabase.table("master_kelas").select("*").eq("nama_kelas", nama_kelas).execute()
    return res.data[0] if res.data else None

def ambil_kelompok_kelas(nama_kelas):
    res = supabase.table("data_kelompok").select("*").eq("nama_kelas", nama_kelas).order("kelompok_id", desc=False).execute()
    return res.data

def ambil_anggota_kelas(nama_kelas):
    res = supabase.table("anggota_kelas").select("*").eq("nama_kelas", nama_kelas).execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=["nama_mahasiswa", "npm_mahasiswa", "nama_kelompok"])

# --- TAMPILAN UTAMA ---
st.title("👥 Sistem Pemilihan Kelompok Kelas Universal")
st.markdown("<p style='text-align: center; color: #9CA3AF; margin-bottom: 0px;'>Sistem pembagian slot kelompok terintegrasi cloud, anti-bentrok, dan real-time untuk seluruh program studi.</p>", unsafe_allow_html=True)

st.markdown("""
    <div style='text-align: center; margin-bottom: 25px;'>
        <span class='dev-badge'>⚡ Designed & Developed by <b>Adam Rahman D.A. S.T.</b></span>
    </div>
""", unsafe_allow_html=True)

st.divider()

# PILIHAN & PENCARIAN RUANG KELAS (SEARCHABLE DROPDOWN)
list_kelas = ambil_semua_kelas()
col_header1, col_header2 = st.columns([2, 1])
with col_header1:
    pilihan_kelas = st.selectbox(
        "🔍 Cari / Pilih Ruang Kelas atau Mata Kuliah Anda:",
        options=["-- Ketik nama kelas / Pilih dari daftar --"] + list_kelas,
        index=0,
        help="Anda dapat mengetik langsung nama mata kuliah/kelas pada kolom ini untuk mencari secara instan."
    )

# --- ALUR UTAMA JIKA KELAS DIPILIH ---
if pilihan_kelas != "-- Ketik nama kelas / Pilih dari daftar --":
    detail_kelas = ambil_detail_kelas(pilihan_kelas)
    list_kelompok = ambil_kelompok_kelas(pilihan_kelas)
    df_anggota = ambil_anggota_kelas(pilihan_kelas)
    
    st.subheader(f"📌 {detail_kelas['nama_kelas']}")
    st.info(f"💬 Petunjuk PJ: {detail_kelas['deskripsi']}")
    
    # SIDEBAR FORM MAHASISWA
    st.sidebar.header("👤 Form Pendaftaran")
    if detail_kelas.get("dikunci", False):
        st.sidebar.error("🔒 Pendaftaran kelompok untuk kelas ini telah DIKUNCI oleh PJ.")
        input_nama, input_npm = "", ""
    else:
        input_nama = st.sidebar.text_input("Masukkan Nama Lengkap:").strip()
        input_npm = st.sidebar.text_input("Masukkan NPM / NIM:").strip()
        
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
                st.sidebar.info("🟢 Identitas aman. Silakan klik tombol 'Ambil Slot' pada kelompok pilihan Anda.")

    # PAPAN KETERSAAN SLOT (RESPONSIF PONSEL & LAPTOP)
    st.write("### 📋 Papan Ketersediaan Slot Kelompok")
    
    num_columns = 3
    for i in range(0, len(list_kelompok), num_columns):
        batch = list_kelompok[i:i + num_columns]
        cols = st.columns(num_columns)
        
        for idx, kel in enumerate(batch):
            with cols[idx]:
                m_terdaftar = df_anggota[df_anggota["nama_kelompok"] == kel["nama_kelompok"]]
                terisi = len(m_terdaftar)
                kapasitas = kel["kapasitas"]
                
                st.markdown(f"""
                <div class='card-kelompok'>
                    <h3 style='margin-bottom:5px; color:#1E3A8A;'>👥 {kel['nama_kelompok']}</h3>
                </div>
                """, unsafe_allow_html=True)
                
                st.progress(min(terisi / kapasitas, 1.0))
                if terisi >= kapasitas:
                    st.markdown(f"Status: <span class='status-penuh'>{terisi} / {kapasitas} (Penuh)</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"Status: <span class='status-tersedia'>{terisi} / {kapasitas} Tersedia</span>", unsafe_allow_html=True)
                
                st.write("")
                for slot_idx in range(kapasitas):
                    if slot_idx < terisi:
                        row_mhs = m_terdaftar.iloc[slot_idx]
                        st.error(f"🔴 **Slot {slot_idx+1}:** {row_mhs['nama_mahasiswa']} ({row_mhs['npm_mahasiswa']})")
                    else:
                        st.success(f"🟢 **Slot {slot_idx+1}:** [ KOSONG ]")
                
                if not detail_kelas.get("dikunci", False) and input_nama and input_npm and not sudah_daftar:
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

    # DOWNLOAD REKAP EXCEL
    st.write("### 📥 Unduh Berkas Rekap Kelas")
    if not df_anggota.empty:
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

    # --- PANEL KONTROL KHUSUS PJ ---
    st.write("##")
    with st.expander("🔑 Panel Manajemen Kontrol PJ Kelas (Butuh PIN Auth)"):
        input_pin = st.text_input("Masukkan PIN Admin Kelas Ini:", type="password", key=f"pin_{pilihan_kelas}")
        if input_pin == detail_kelas["pin_admin"]:
            st.success("🔓 Hak Akses PJ Terverifikasi! Anda diizinkan mengubah pengaturan.")
            
            edit_desk = st.text_area("Ubah Deskripsi Petunjuk:", value=detail_kelas["deskripsi"])
            toggle_kunci = st.toggle("🔒 Kunci Akses Pengisian Mahasiswa", value=detail_kelas.get("dikunci", False))
            
            col_e1, col_e2 = st.columns(2)
            with col_e1:
                edit_j_kel = st.number_input(
                    "Ubah Jumlah Kelompok:", 
                    min_value=1, 
                    max_value=40, 
                    value=int(detail_kelas.get("jumlah_kelompok", len(list_kelompok)))
                )
            with col_e2:
                edit_kap = st.number_input(
                    "Ubah Kapasitas per Kelompok:", 
                    min_value=1, 
                    max_value=100, 
                    value=int(detail_kelas.get("kapasitas_per_kelompok", 4))
                )
            
            if st.button("💾 Simpan Perubahan Setelan Kelas", type="primary"):
                supabase.table("master_kelas").update({
                    "deskripsi": edit_desk,
                    "dikunci": toggle_kunci,
                    "jumlah_kelompok": int(edit_j_kel),
                    "kapasitas_per_kelompok": int(edit_kap)
                }).eq("nama_kelas", pilihan_kelas).execute()
                
                supabase.table("data_kelompok").update({
                    "kapasitas": int(edit_kap)
                }).eq("nama_kelas", pilihan_kelas).execute()
                
                current_count = len(list_kelompok)
                new_count = int(edit_j_kel)
                
                if new_count > current_count:
                    new_groups = [
                        {
                            "nama_kelas": pilihan_kelas,
                            "nama_kelompok": f"Kelompok {i}",
                            "kapasitas": int(edit_kap)
                        }
                        for i in range(current_count + 1, new_count + 1)
                    ]
                    supabase.table("data_kelompok").insert(new_groups).execute()
                
                elif new_count < current_count:
                    groups_to_remove = [f"Kelompok {i}" for i in range(new_count + 1, current_count + 1)]
                    for g_name in groups_to_remove:
                        supabase.table("anggota_kelas").delete().eq("nama_kelas", pilihan_kelas).eq("nama_kelompok", g_name).execute()
                        supabase.table("data_kelompok").delete().eq("nama_kelas", pilihan_kelas).eq("nama_kelompok", g_name).execute()
                
                st.success("Setelan kelas & struktur kelompok berhasil diperbarui!")
                st.rerun()
                
            st.divider()
            st.write("**⚠️ Menu Bahaya Kontrol Sesi:**")
            if st.button("🔴 RESET & HAPUS TOTAL RUANG KELAS INI"):
                supabase.table("master_kelas").delete().eq("nama_kelas", pilihan_kelas).execute()
                st.success("Ruang kelas sukses dihapus!")
                st.rerun()
        elif input_pin != "":
            st.error("PIN Salah!")

# --- PEMBUATAN RUANG KELAS BARU DEGAN INTERAKSI DAN ANIMASI SUKSES ---
st.divider()
with st.expander("➕ PJ Baru? Klik di Sini untuk Membuat Ruang Pembagian Kelompok Baru"):
    st.write("Buat ruang pendaftaran terpisah khusus untuk kelas atau mata kuliah Anda sendiri:")
    new_nama_kelas = st.text_input("Nama Mata Kuliah & Kelas:", placeholder="Contoh: Pembagian kelompok R3L Ekonomika")
    new_deskripsi = st.text_area("Deskripsi / Aturan Kelompok:", value="Pilih slot kelompokmu yang masih tersedia. Ingat, satu mahasiswa hanya bisa memilih 1 slot!")
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        new_j_kel = st.number_input("Jumlah Kelompok yang Ingin Dibuat:", min_value=1, max_value=40, value=5)
    with col_c2:
        new_kap = st.number_input("Kapasitas Batas Anggota per Kelompok:", min_value=1, max_value=100, value=4)
        
    new_pin = st.text_input("Buat PIN Keamanan Admin Ruang Ini:", type="password", help="PIN ini wajib Anda simpan untuk mengontrol kelas ini.")
    
    if st.button("🚀 Buat dan Aktifkan Ruang Kelas", type="primary"):
        if new_nama_kelas and new_pin:
            try:
                with st.spinner("Memproses & mendaftarkan ruang kelas baru..."):
                    supabase.table("master_kelas").insert({
                        "nama_kelas": new_nama_kelas,
                        "deskripsi": new_deskripsi,
                        "pin_admin": new_pin,
                        "jumlah_kelompok": int(new_j_kel),
                        "kapasitas_per_kelompok": int(new_kap),
                        "dikunci": False
                    }).execute()
                    
                    data_kelompok_batch = [
                        {
                            "nama_kelas": new_nama_kelas,
                            "nama_kelompok": f"Kelompok {num}",
                            "kapasitas": int(new_kap)
                        }
                        for num in range(1, int(new_j_kel) + 1)
                    ]
                    supabase.table("data_kelompok").insert(data_kelompok_batch).execute()
                
                # ANIMASI & BALASAN VISUAL SUKSES
                st.balloons()
                st.success(f"🎉 **BERHASIL!** Ruang kelas '{new_nama_kelas}' telah aktif dan siap digunakan.")
                time.sleep(1.8) # Jeda singkat agar pengguna dapat menikmati animasi sukses
                st.rerun()
            except Exception as e:
                err_msg = str(e)
                if "duplicate" in err_msg.lower() or "unique" in err_msg.lower():
                    st.error("⚠️ Nama kelas sudah terdaftar! Gunakan nama yang lebih spesifik.")
                else:
                    st.error(f"Gagal menyimpan ke database: {err_msg}")
        else:
            st.error("⚠️ Nama Kelas dan PIN Admin wajib diisi!")
