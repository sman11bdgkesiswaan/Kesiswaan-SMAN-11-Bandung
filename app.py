import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import datetime

st.set_page_config(page_title="Kesiswaan SMAN 11 Bandung", page_icon="🏫", layout="wide")

# Master Data Kategori, Pelanggaran, dan Poin
MASTER_PELANGGARAN = {
    "Ringan": {
        "Datang terlambat (< 15 menit)": 5,
        "Seragam tidak rapi / atribut tidak lengkap": 5,
        "Tidak membawa buku pelajaran": 5,
        "Rambut tidak rapi / Make-up berlebih": 5,
        "Membawa HP saat KBM tanpa izin": 10
    },
    "Sedang": {
        "Terlambat (> 15 menit)": 15,
        "Mencoret-coret fasilitas sekolah": 15,
        "Meninggalkan kelas / Bolos jam pelajaran": 20,
        "Keluar lingkungan sekolah tanpa izin": 25,
        "Sikap tidak sopan kepada guru / staf": 25
    },
    "Berat": {
        "Merokok di area sekolah": 50,
        "Perkelahian / Keributan antar siswa": 50,
        "Membawa sajam / barang berbahaya": 75,
        "Merusak sarana prasarana sekolah": 75,
        "Kecurangan ujian / Pemalsuan dokumen": 75
    },
    "Berat Sekali": {
        "Tawuran antar pelajar": 100,
        "Membawa / Mengonsumsi Miras & Narkoba": 100,
        "Tindak kriminalitas / Perjudian / Pelecehan": 100,
        "Tindak perundungan / Bullying berat": 100
    }
}

# Koneksi ke Google Sheets / File Local
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=60)
def load_data_siswa():
    # Membaca data siswa (X-1 s.d XII-12)
    return conn.read(worksheet="NAMA SISWA", usecols=["NO", "NAMA SISWA", "KELAS"])

@st.cache_data(ttl=10)
def load_data_pelanggaran():
    return conn.read(worksheet="PELANGGARAN")

st.title("🏫 Sistem Informasi Pelanggaran Siswa - SMAN 11 Bandung")

df_siswa = load_data_siswa()
df_pelanggaran = load_data_pelanggaran()

menu = st.sidebar.selectbox("Menu Utama", ["📊 Dashboard Kesiswaan", "📝 Input Pelanggaran", "📁 Rekap Data"])

# ---------------- DASHBOARD ----------------
if menu == "📊 Dashboard Kesiswaan":
    st.header("Dashboard Pelanggaran Siswa")
    
    col_k, col_s = st.columns(2)
    with col_k:
        pilih_kelas = st.selectbox("Filter Kelas", ["Semua Kelas"] + sorted(df_siswa['KELAS'].unique().tolist()))
    
    df_view = df_pelanggaran.copy()
    if pilih_kelas != "Semua Kelas":
        df_view = df_view[df_view['Kelas'] == pilih_kelas]
        
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Kasus", len(df_view))
    m2.metric("Total Akumulasi Poin", int(df_view['Poin'].sum()) if not df_view.empty else 0)
    m3.metric("Siswa Perlu Pembinaan (>50 Poin)", 
              len(df_view.groupby('Nama Siswa')['Poin'].sum()[lambda x: x >= 50]) if not df_view.empty else 0)

    st.markdown("---")
    st.subheader("Top Siswa Poin Pelanggaran Tertinggi")
    if not df_view.empty:
        top_siswa = df_view.groupby(['Nama Siswa', 'Kelas'])['Poin'].sum().reset_index().sort_values(by='Poin', ascending=False)
        st.dataframe(top_siswa, use_container_width=True)

# ---------------- INPUT PELANGGARAN ----------------
elif menu == "📝 Input Pelanggaran":
    st.header("Input Catatan Pelanggaran Baru")
    
    with st.form("form_input", clear_on_submit=True):
        tgl = st.date_input("Tanggal Kejadian", datetime.date.today())
        
        # 1. Pilih Kelas (X-1 s.d XII-12)
        daftar_kelas = sorted(df_siswa['KELAS'].unique().tolist())
        kelas = st.selectbox("Pilih Kelas", daftar_kelas)
        
        # 2. Sinkronisasi Nama Siswa berdasarkan Kelas yang dipilih
        siswa_kelas = df_siswa[df_siswa['KELAS'] == kelas]['NAMA SISWA'].tolist()
        nama_siswa = st.selectbox("Pilih Nama Lengkap Siswa", siswa_kelas)
        
        # 3. Kategori & Jenis Pelanggaran Sinkron
        kategori = st.selectbox("Kategori Pelanggaran", ["Ringan", "Sedang", "Berat", "Berat Sekali"])
        jenis_opsi = list(MASTER_PELANGGARAN[kategori].keys())
        jenis = st.selectbox("Jenis Pelanggaran", jenis_opsi)
        
        # 4. Poin Otomatis
        poin = MASTER_PELANGGARAN[kategori][jenis]
        st.info(f"📌 Poin Otomatis: **{poin} Poin**")
        
        catatan = st.text_area("Catatan / Tindakan Kesiswaan")
        
        simpan = st.form_submit_button("💾 Simpan Pelanggaran ke Excel / Google Sheets")
        
        if simpan:
            row_baru = pd.DataFrame([{
                "Tanggal": str(tgl), "Kelas": kelas, "Nama Siswa": nama_siswa,
                "Kategori": kategori, "Jenis Pelanggaran": jenis, "Poin": poin, "Catatan/Tindakan": catatan
            }])
            df_updated = pd.concat([df_pelanggaran, row_baru], ignore_index=True)
            conn.update(worksheet="PELANGGARAN", data=df_updated)
            st.success(f"Pelanggaran {nama_siswa} ({kelas}) berhasil disimpan!")

# ---------------- REKAP DATA ----------------
elif menu == "📁 Rekap Data":
    st.header("Rekap Seluruh Data Pelanggaran")
    st.dataframe(df_pelanggaran, use_container_width=True)
