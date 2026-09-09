import streamlit as st
import pandas as pd
import time

# 1. Konfigurasi Halaman Utama
st.set_page_config(page_title="Sistem Pemilihan Kelompok Kelas", layout="wide", page_icon="👥")

# 2. Inisialisasi State / Database Lokal dalam Sesi
if "config" not in st.session_state:
    st.session_state.config = {
        "judul": "Pembagian Kelompok Mata Kuliah",
        "deskripsi": "Pilih slot kelompokmu yang masih tersedia. Ingat, satu mahasiswa hanya bisa memilih 1 slot!",
        "pass_admin": "admin123",
        "dikunci": False
    }

if "kelompok_list" not in st.session_state:
    # Default 5 kelompok, kapasitas 4 orang
    st.session_state.kelompok_list = [
        {"id": i, "nama": f"Kelompok {i}", "kapasitas": 4} for i in range(1, 6)
    ]

if "data_anggota" not in st.session_state:
    st.session_state.data_anggota = pd.DataFrame(columns=["NIM_Nama", "Kelompok_ID"])

# Shortcut variabel
cfg = st.session_state.config
df_anggota = st.session_state.data_anggota

# --- HEADER UTAMA ---
st.title(f"📌 {cfg['judul']}")
st.markdown(f"*{cfg['deskripsi']}*")
st.divider()

# --- SIDEBAR: AKSES PENDAFTARAN MAHASISWA & PANEL ADMIN ---
st.sidebar.header("👤 Input Data Mahasiswa")

if cfg["dikunci"]:
    st.sidebar.error("🔒 Pemilihan kelompok telah DIKUNCI oleh PJ/Admin.")
    input_identitas = ""
else:
    input_identitas = st.sidebar.text_input("Masukkan Nama / NIM Anda:").strip()

    if input_identitas:
        # Cek apakah nama/NIM sudah terdaftar
        sudah_daftar = df_anggota[df_anggota["NIM_Nama"].str.lower() == input_identitas.lower()]

        if not sudah_daftar.empty:
            kel_id_user = sudah_daftar.iloc[0]["Kelompok_ID"]
            nama_kel_user = next((k["nama"] for k in st.session_state.kelompok_list if k["id"] == kel_id_user), "Kelompok")
            st.sidebar.warning(f"Anda sudah terdaftar di **{nama_kel_user}**.")
            
            # Tombol Batal Slot Sendiri
            if st.sidebar.button("❌ Batalkan Slot Saya"):
                st.session_state.data_anggota = df_anggota[df_anggota["NIM_Nama"].str.lower() != input_identitas.lower()]
                st.sidebar.success("Slot berhasil dibatalkan!")
                st.rerun()
        else:
            st.sidebar.info("Status: Belum memilih kelompok.")

st.sidebar.divider()

# --- PANEL PJ / ADMIN (UNIVERSAL) ---
with st.sidebar.expander("🔑 Panel Kontrol PJ / Admin"):
    pass_input = st.text_input("Password Admin:", type="password")
    
    if pass_input == cfg["pass_admin"]:
        st.success("Akses Admin Diterima")
        
        # Edit Judul & Deskripsi
        new_judul = st.text_input("Judul Mata Kuliah / Kegiatan:", value=cfg["judul"])
        new_desk = st.text_area("Deskripsi / Petunjuk:", value=cfg["deskripsi"])
        new_pass = st.text_input("Ganti Password Admin:", value=cfg["pass_admin"])
        
        # Sakelar Kunci Pilihan
        is_lock = st.toggle("🔒 Kunci Semua Pilihan", value=cfg["dikunci"])
        
        if st.button("Simpan Pengaturan Header"):
            st.session_state.config["judul"] = new_judul
            st.session_state.config["deskripsi"] = new_desk
            st.session_state.config["pass_admin"] = new_pass
            st.session_state.config["dikunci"] = is_lock
            st.rerun()

        st.divider()
        st.write("**Atur Kelompok:**")
        
        # Tambah / Hapus Kelompok
        col_adm1, col_adm2 = st.columns(2)
        with col_adm1:
            if st.button("➕ Kelompok"):
                new_id = len(st.session_state.kelompok_list) + 1
                st.session_state.kelompok_list.append({"id": new_id, "nama": f"Kelompok {new_id}", "kapasitas": 4})
                st.rerun()
        with col_adm2:
            if st.button("➖ Kelompok") and len(st.session_state.kelompok_list) > 1:
                st.session_state.kelompok_list.pop()
                st.rerun()

        # Edit Nama & Kapasitas per Kelompok
        for k in st.session_state.kelompok_list:
            st.caption(f"Setting {k['nama']}")
            k["nama"] = st.text_input(f"Nama Kelompok (ID {k['id']}):", value=k["nama"], key=f"knama_{k['id']}")
            k["kapasitas"] = st.number_input(f"Kapasitas Slot:", min_value=1, value=k["kapasitas"], key=f"kkap_{k['id']}")

        if st.button("🔴 Reset Semua Data Anggota"):
            st.session_state.data_anggota = pd.DataFrame(columns=["NIM_Nama", "Kelompok_ID"])
            st.rerun()

# --- PAPAN VISUAL KELOMPOK (REAL-TIME DISPLAY DENGAN FRAGMENT BAWAN) ---
st.subheader("📋 Papan Slot Kelompok")

# Fungsi Fragment bawaan Streamlit untuk autorefresh real-time otomatis setiap 3 detik secara aman
@st.fragment(run_every=3)
def tampilkan_papan_realtime(input_id_user):
    # Mengambil data terbaru dari session state
    df_aktif = st.session_state.data_anggota
    cols = st.columns(3) # Tampilkan dalam 3 kolom visual

    for idx, kel in enumerate(st.session_state.kelompok_list):
        col = cols[idx % 3]
        
        # Ambil anggota di kelompok ini
        members = df_aktif[df_aktif["Kelompok_ID"] == kel["id"]]["NIM_Nama"].tolist()
        terisi = len(members)
        kapasitas = kel["kapasitas"]
        
        with col:
            with st.container(border=True):
                st.markdown(f"### 👥 {kel['nama']}")
                st.progress(min(terisi / kapasitas, 1.0))
                st.caption(f"Status Slot: **{terisi} / {kapasitas} Terisi**")
                
                # List Anggota Terdaftar
                for i in range(kapasitas):
                    if i < terisi:
                        st.error(f"🔴 **Slot {i+1}:** {members[i]}")
                    else:
                        st.success(f"🟢 **Slot {i+1}:** [ KOSONG ]")
                
                # Tombol Pilih Slot untuk Mahasiswa
                if not st.session_state.config["dikunci"] and input_id_user:
                    sudah_daftar = not df_aktif[df_aktif["NIM_Nama"].str.lower() == input_id_user.lower()].empty
                    
                    if not sudah_daftar and terisi < kapasitas:
                        if st.button(f"Pilih {kel['nama']}", key=f"btn_join_{kel['id']}"):
                            new_row = pd.DataFrame([{"NIM_Nama": input_id_user, "Kelompok_ID": kel["id"]}])
                            st.session_state.data_anggota = pd.concat([st.session_state.data_anggota, new_row], ignore_index=True)
                            st.rerun()

# Menjalankan fungsi papan real-time
tampilkan_papan_realtime(input_identitas)

st.divider()

# --- EKSPOR DATA UNTUK DOSEN ---
st.subheader("📥 Download Hasil Pembagian Kelompok")

if not st.session_state.data_anggota.empty:
    # Menggabungkan data nama kelompok untuk hasil ekspor
    export_df = st.session_state.data_anggota.copy()
    map_kel = {k["id"]: k["nama"] for k in st.session_state.kelompok_list}
    export_df["Nama Kelompok"] = export_df["Kelompok_ID"].map(map_kel)
    export_df = export_df[["Nama Kelompok", "NIM_Nama"]].rename(columns={"NIM_Nama": "Nama / NIM Mahasiswa"})
    
    csv_bytes = export_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📄 Download File Excel / CSV",
        data=csv_bytes,
        file_name=f"kelompok_{cfg['judul'].replace(' ', '_')}.csv",
        mime="text/csv"
    )
else:
    st.info("Belum ada mahasiswa yang terdaftar.")
