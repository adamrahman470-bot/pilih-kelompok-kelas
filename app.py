import io
import pandas as pd
import streamlit as st

# 1. KONFIGURASI HALAMAN UTAMA & TEMA KUSTOM
st.set_page_config(
    page_title="Sistem Pemilihan Kelompok Kelas Universal",
    layout="wide",
    page_icon="👥",
)

# Styling CSS untuk UI Premium & Modern
st.markdown(
    """
    <style>
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    h1 { color: #1E3A8A; font-weight: 800; }
    .stButton>button { width: 100%; border-radius: 6px; font-weight: 600; }
    .status-penuh { color: #DC2626; font-weight: bold; background-color: #FEE2E2; padding: 2px 8px; border-radius: 4px; }
    .status-tersedia { color: #16A34A; font-weight: bold; background-color: #DCFCE7; padding: 2px 8px; border-radius: 4px; }
    .box-sesi { background-color: #F3F4F6; padding: 15px; border-radius: 8px; border-left: 5px solid #2563EB; }
    </style>""",
    unsafe_allow_html=True,
)

# 2. INISIALISASI STATE UTAMA
if "sesi_aktif" not in st.session_state:
    st.session_state.sesi_aktif = False

if "config" not in st.session_state:
    st.session_state.config = {}

if "kelompok_list" not in st.session_state:
    st.session_state.kelompok_list = []

if "data_anggota" not in st.session_state:
    st.session_state.data_anggota = pd.DataFrame(
        columns=["Nama", "NPM", "Kelompok_ID", "Nama_Kelompok"]
    )

# --- SIDEBAR UTAMA: FORM INPUT MAHASISWA & PANEL ADMIN ---
st.sidebar.header("👤 Menu Pendaftaran")

# JIKA BELUM ADA SESI YANG DIBUAT OLEH PJ
if not st.session_state.sesi_aktif:
    st.title("👥 Sistem Pemilihan Kelompok Kelas Real-Time")
    st.info("💡 Belum ada sesi pembagian kelompok yang aktif saat ini.")

    st.markdown("""
    ### 📢 Petunjuk untuk Penanggung Jawab (PJ):
    Silakan masuk ke **Panel Kontrol PJ / Admin** di sidebar sebelah kiri untuk membuat sesi pembagian kelompok baru khusus untuk mata kuliah Anda.
    """)

    # Form Pembuatan Sesi Baru untuk PJ Siapapun
    with st.sidebar.expander(
        "➕ Buat Sesi Pembagian Kelompok Baru", expanded=True
    ):
        st.write(
            "Isi formulir di bawah ini untuk menginisiasi ruang pendaftaran"
            " kelompok baru:"
        )
        buat_judul = st.text_input(
            "Nama Mata Kuliah / Kegiatan:",
            placeholder="Contoh: Pemrograman Web Kelas A",
        )
        buat_deskripsi = st.text_area(
            "Deskripsi / Petunjuk Tugas:",
            value=(
                "Pilih slot kelompokmu yang masih tersedia. Ingat, satu"
                " mahasiswa hanya bisa memilih 1 slot!"
            ),
        )

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            buat_jumlah_kel = st.number_input(
                "Jumlah Kelompok Awal:", min_value=1, max_value=50, value=5
            )
        with col_s2:
            buat_kapasitas = st.number_input(
                "Kapasitas per Kelompok:", min_value=1, max_value=100, value=4
            )

        buat_pin = st.text_input(
            "Buat PIN / Password Admin Anda:",
            type="password",
            help=(
                "PIN ini digunakan hanya oleh Anda untuk mengatur sesi ini."
            ),
        )

        if st.button("🚀 Aktifkan Sesi Kelompok Sekarang", type="primary"):
            if buat_judul and buat_pin:
                # Daftarkan konfigurasi mandiri milik PJ tersebut
                st.session_state.config = {
                    "judul": buat_judul,
                    "deskripsi": buat_deskripsi,
                    "pass_admin": buat_pin,
                    "dikunci": False,
                }
                # Generate kelompok default pesanan PJ
                st.session_state.kelompok_list = [
                    {
                        "id": i,
                        "nama": f"Kelompok {i}",
                        "kapasitas": int(buat_kapasitas),
                    }
                    for i in range(1, int(buat_jumlah_kel) + 1)
                ]
                # Reset kontainer data anggota agar bersih dari sisa sesi kelas lain
                st.session_state.data_anggota = pd.DataFrame(
                    columns=["Nama", "NPM", "Kelompok_ID", "Nama_Kelompok"]
                )
                st.session_state.sesi_aktif = True
                st.success("Sesi berhasil dibuat! Halaman otomatis memuat data.")
                st.rerun()
            else:
                st.error("Nama Mata Kuliah dan PIN Admin wajib diisi!")
    st.stop()

# JIKA SESI SUDAH AKTIF (ALUR MAHASISWA & MANAJEMEN PJ)
cfg = st.session_state.config

# --- TAMPILAN HEADER UTAMA DARI CONFIG PJ ---
st.title(f"📌 {cfg['judul']}")
st.markdown(f"*{cfg['deskripsi']}*")
st.divider()

# Logika Input Mahasiswa (Hanya tampil jika pendaftaran belum dikunci oleh PJ)
if cfg["dikunci"]:
    st.sidebar.error("🔒 Pemilihan kelompok telah DIKUNCI oleh PJ/Admin.")
    input_nama = ""
    input_npm = ""
else:
    input_nama = st.sidebar.text_input("Masukkan Nama:").strip()
    input_npm = st.sidebar.text_input("Masukkan NPM:").strip()

    df_aktif = st.session_state.data_anggota
    sudah_daftar_nama = (
        not df_aktif[df_aktif["Nama"].str.lower() == input_nama.lower()].empty
        if input_nama
        else False
    )
    sudah_daftar_npm = (
        not df_aktif[df_aktif["NPM"] == input_npm].empty
        if input_npm
        else False
    )

    if input_nama or input_npm:
        if sudah_daftar_nama or sudah_daftar_npm:
            user_row = df_aktif[
                (df_aktif["Nama"].str.lower() == input_nama.lower())
                | (df_aktif["NPM"] == input_npm)
            ].iloc[0]
            st.sidebar.warning(
                f"Identitas ini sudah terdaftar di **{user_row['Nama_Kelompok']}**."
            )

            if st.sidebar.button("❌ Batalkan Slot Saya", type="secondary"):
                st.session_state.data_anggota = df_aktif[
                    (df_aktif["Nama"].str.lower() != input_nama.lower())
                    & (df_aktif["NPM"] != input_npm)
                ]
                st.sidebar.success("Slot berhasil dibatalkan!")
                st.rerun()
        else:
            st.sidebar.info(
                "💡 Identitas aman. Silakan klik tombol 'Pilih Kelompok' pada"
                " papan utama di sebelah kanan."
            )

st.sidebar.divider()

# --- PANEL KONTROL KHUSUS PJ / ADMIN YANG MEMILIKI PIN ---
with st.sidebar.expander("🔑 Panel Kontrol PJ / Admin"):
    pass_input = st.text_input("Masukkan PIN Admin Sesi Ini:", type="password")

    if pass_input == cfg["pass_admin"]:
        st.success("🔓 Mode Kontrol PJ Aktif")

        # PJ mengubah teks judulan dan petunjuk mandiri
        new_judul = st.text_input("Ubah Judul Mata Kuliah:", value=cfg["judul"])
        new_desk = st.text_area(
            "Ubah Deskripsi / Petunjuk:", value=cfg["deskripsi"]
        )
        new_pass = st.text_input(
            "Ubah PIN Admin Sesi Ini:", value=cfg["pass_admin"]
        )
        is_lock = st.toggle(
            "🔒 Kunci Semua Pilihan (Lock All)", value=cfg["dikunci"]
        )

        if st.button("💾 Simpan Perubahan Setelan", type="primary"):
            st.session_state.config["judul"] = new_judul
            st.session_state.config["deskripsi"] = new_desk
            st.session_state.config["pass_admin"] = new_pass
            st.session_state.config["dikunci"] = is_lock
            st.rerun()

        st.divider()
        st.write("**⚙️ Manajemen Jumlah Kelompok:**")

        col_adm1, col_adm2 = st.columns(2)
        with col_adm1:
            if st.button("➕ Tambah Kelompok"):
                new_id = len(st.session_state.kelompok_list) + 1
                st.session_state.kelompok_list.append(
                    {
                        "id": new_id,
                        "nama": f"Kelompok {new_id}",
                        "kapasitas": 4,
                    }
                )
                st.rerun()
        with col_adm2:
            if (
                st.button("➖ Kurang Kelompok")
                and len(st.session_state.kelompok_list) > 1
            ):
                st.session_state.kelompok_list.pop()
                st.rerun()

        # Kustomisasi Nama Kelompok & Batas Kapasitas per Kelompok secara dinamis oleh PJ
        st.write("**📝 Detail Kustomisasi Kelompok:**")
        for k in st.session_state.kelompok_list:
            with st.container(border=True):
                k["nama"] = st.text_input(
                    f"Nama Kelompok (ID {k['id']}):",
                    value=k["nama"],
                    key=f"knama_{k['id']}",
                )
                k["kapasitas"] = st.number_input(
                    "Batas Kapasitas Slot:",
                    min_value=1,
                    value=k["kapasitas"],
                    key=f"kkap_{k['id']}",
                )

        st.divider()
        # Fitur Hapus Total untuk membebaskan ruang bagi PJ Mata Kuliah Selanjutnya
        if st.button(
            "🔴 TUTUP & RESET TOTAL SESI INI",
            type="secondary",
            help=(
                "Menghapus sesi ini agar PJ mata kuliah lain bisa membuat sesi"
                " baru."
            ),
        ):
            st.session_state.config = {}
            st.session_state.kelompok_list = []
            st.session_state.data_anggota = pd.DataFrame(
                columns=["Nama", "NPM", "Kelompok_ID", "Nama_Kelompok"]
            )
            st.session_state.sesi_aktif = False
            st.rerun()
    elif pass_input != "":
        st.error(
            "PIN Salah! Hanya PJ pembuat sesi yang dapat memodifikasi data."
        )

# --- PAPAN VISUAL KELOMPOK (REAL-TIME GRID DISPLAY) ---
st.subheader("📋 Papan Slot Kelompok Kelas")


@st.fragment(run_every=3)
def render_papan_interaktif(nama_user, npm_user):
    df_current = st.session_state.data_anggota
    cols = st.columns(3)  # Grid otomatis membagi 3 kolom responsif PC/HP

    for idx, kel in enumerate(st.session_state.kelompok_list):
        col = cols[idx % 3]
        members_df = df_current[df_current["Kelompok_ID"] == kel["id"]]
        terisi = len(members_df)
        kapasitas = kel["kapasitas"]

        with col:
            with st.container(border=True):
                st.markdown(f"### 👥 {kel['nama']}")
                st.progress(min(terisi / kapasitas, 1.0))

                if terisi >= kapasitas:
                    st.markdown(
                        "Status Slot: <span"
                        f" class='status-penuh'>{terisi} / {kapasitas}"
                        " (Penuh)</span>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        "Status Slot: <span"
                        f" class='status-tersedia'>{terisi} / {kapasitas}"
                        " Tersedia</span>",
                        unsafe_allow_html=True,
                    )

                st.write("")
                # Tampilkan slot isi / kosong
                for i in range(kapasitas):
                    if i < terisi:
                        m_row = members_df.iloc[i]
                        st.error(
                            f"🔴 **Slot {i+1}:** {m_row['Nama']}"
                            f" ({m_row['NPM']})"
                        )
                    else:
                        st.success(f"🟢 **Slot {i+1}:** [ KOSONG ]")

                # Validasi Tombol Pendaftaran tanpa perlu Enter Keyboard
                if (
                    not st.session_state.config.get("dikunci", False)
                    and nama_user
                    and npm_user
                ):
                    is_registered = not df_current[
                        (df_current["Nama"].str.lower() == nama_user.lower())
                        | (df_current["NPM"] == npm_user)
                    ].empty
                    tombol_mati = is_registered or (terisi >= kapasitas)
                    if st.button(
                        f"Pilih {kel['nama']}",
                        key=f"btn_pilih_{kel['id']}",
                        disabled=tombol_mati,
                        type="primary",
                    ):
                        new_member = pd.DataFrame(
                            [{
                                "Nama": nama_user,
                                "NPM": npm_user,
                                "Kelompok_ID": kel["id"],
                                "Nama_Kelompok": kel["nama"],
                            }]
                        )
                        st.session_state.data_anggota = pd.concat(
                            [st.session_state.data_anggota, new_member],
                            ignore_index=True,
                        )
                        st.rerun()


# Menjalankan Papan Utama
render_papan_interaktif(
    input_nama if "input_nama" in locals() else "",
    input_npm if "input_npm" in locals() else "",
)

st.divider()

# --- EKSPOR DATA REKAPITULASI (URUT DAN RAPI PER KELOMPOK) ---
st.subheader("📥 Download Hasil Pendaftaran PJ")
if not st.session_state.data_anggota.empty:
    df_download = st.session_state.data_anggota.copy()
    # Otomatis disortir berurutan dari Kelompok 1, 2, 3 dst beserta nama mahasiswa di dalamnya
    df_download = df_download.sort_values(
        by=["Kelompok_ID", "Nama"]
    ).reset_index(drop=True)
    df_final_view = df_download[
        ["Nama_Kelompok", "Nama", "NPM"]
    ].rename(
        columns={
            "Nama_Kelompok": "Kelompok",
            "Nama": "Nama Lengkap Mahasiswa",
            "NPM": "NPM / NIM",
        }
    )

    # Preview tabel rekapitulasi rapi di layar sebelum diunduh
    st.dataframe(df_final_view, use_container_width=True)

    # Proses konversi data ke format Excel asli (.xlsx)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_final_view.to_excel(
            writer, index=False, sheet_name="Rekap Kelompok Kelas"
        )

    st.download_button(
        label="🟢 Download File Rekapitulasi Excel (.xlsx)",
        data=buffer.getvalue(),
        file_name=f"REKAP_KELOMPOK_{cfg['judul'].replace(' ', '_')}.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    )
else:
    st.info("Belum ada mahasiswa yang mengisi slot pendaftaran kelompok.")
