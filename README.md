# 👥 Sistem Pemilihan Kelompok Kelas Universal

> Aplikasi web berbasis real-time untuk pembagian slot kelompok mahasiswa secara fleksibel, anti-bentrok, dan terintegrasi dengan cloud database.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://pilih-kelompok-kelas-kzf4skhe5y68hn3x2dfjhc.streamlit.app/)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Database](https://img.shields.io/badge/Database-Supabase%20%28PostgreSQL%29-green)

---

## 🔗 Live Demo
Coba aplikasi secara langsung: **[Sistem Pemilihan Kelompok Kelas](https://pilih-kelompok-kelas-kzf4skhe5y68hn3x2dfjhc.streamlit.app/)**

---

## 📌 Fitur Utama
- **Pilihan Kelas & Ruang Dinamis:** Penanggung Jawab (PJ) kelas dapat membuat ruang pendaftaran baru dengan kuota dan kapasitas khusus.
- **Visualisasi Slot Real-Time:** Papan status interaktif dengan indikator keterisian slot per kelompok secara langsung.
- **Sistem Keamanan PIN Admin:** Modul kontrol khusus PJ yang dilindungi PIN untuk mengunci pendaftaran atau mengatur ulang kelas.
- **Pencegahan Data Ganda (Anti-Curang):** Validasi otomatis berdasarkan NPM/NIM mahasiswa agar tidak ada yang mengambil slot ganda.
- **Ekspor Rekap Otomatis:** Fitur unduh rekap pendaftaran kelompok langsung ke format berkas Excel (`.xlsx`).

---

## 🛠️ Teknologi yang Digunakan
- **Frontend & UI Framework:** [Streamlit](https://streamlit.io/)
- **Backend & Database:** [Supabase](https://supabase.com/) (PostgreSQL cloud)
- **Data Processing & Export:** [Pandas](https://pandas.pydata.org/), [OpenPyXL](https://openpyxl.readthedocs.io/)
- **Deployment Platform:** Streamlit Community Cloud

---

## 🗄️ Skema Database (Supabase)
Proyek ini memanfaatkan 3 tabel utama di Supabase:
1. `master_kelas`: Menyimpan informasi ruang kelas, deskripsi, PIN admin, dan batas kuota.
2. `data_kelompok`: Menyimpan daftar kelompok yang ter-generate otomatis untuk tiap kelas.
3. `anggota_kelas`: Menyimpan data pendaftaran mahasiswa per kelompok.

---

## 💻 Cara Menjalankan di Lokal (Local Setup)

1. **Clone repository ini:**
   ```bash
   git clone [https://github.com/adamrahman470-bot/pilih-kelompok-kelas.git](https://github.com/adamrahman470-bot/pilih-kelompok-kelas.git)
   cd pilih-kelompok-kelas
