import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Set style
sns.set_style('whitegrid')
plt.rcParams['figure.figsize'] = (14, 6)

# Load dataset - coba beberapa file yang mungkin punya kolom tanggal
try:
    # Coba dataset_raw.csv dulu
    df = pd.read_csv('dataset/dataset_raw.csv')
    print(f"Loaded dataset/dataset_raw.csv: {len(df)} rows")
except:
    try:
        # Kalau tidak ada, coba dataset_filtered.csv
        df = pd.read_csv('dataset/dataset_filtered.csv')
        print(f"Loaded dataset/dataset_filtered.csv: {len(df)} rows")
    except:
        # Terakhir coba dataset_labeled.csv
        df = pd.read_csv('dataset/dataset_labeled.csv')
        print(f"Loaded dataset/dataset_labeled.csv: {len(df)} rows")

# Tampilkan kolom yang tersedia
print("\nKolom yang tersedia:")
print(df.columns.tolist())
print("\nContoh data:")
print(df.head())

# Cari kolom tanggal (bisa berbagai nama)
date_columns = [col for col in df.columns if any(keyword in col.lower() 
                for keyword in ['date', 'time', 'published', 'created', 'posted'])]

if date_columns:
    date_col = date_columns[0]
    print(f"\nMenggunakan kolom tanggal: {date_col}")
    
    # Parse tanggal
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    
    # Hapus data dengan tanggal invalid
    df = df.dropna(subset=[date_col])
    
    # Extract date (tanpa jam)
    df['date'] = df[date_col].dt.date
    
    # Hitung jumlah komentar per hari
    daily_counts = df.groupby('date').size().reset_index(name='count')
    daily_counts['date'] = pd.to_datetime(daily_counts['date'])
    daily_counts = daily_counts.sort_values('date')
    
    # Buat grafik
    fig, ax = plt.subplots(figsize=(16, 8))
    
    ax.plot(daily_counts['date'], daily_counts['count'], 
            marker='o', linewidth=2.5, markersize=7, color='#3498db', alpha=0.8)
    
    ax.set_xlabel('Tanggal', fontsize=16, fontweight='bold')
    ax.set_ylabel('Jumlah Komentar', fontsize=16, fontweight='bold')
    ax.set_title('Tren Aktivitas Komentar Publik di YouTube\nterkait Isu Dana Rp 200 Triliun', 
                 fontsize=18, fontweight='bold', pad=25)
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Rotasi label tanggal agar tidak overlap dengan font lebih besar
    plt.xticks(rotation=45, ha='right', fontsize=13)
    plt.yticks(fontsize=13)
    
    # Tambahkan caption di bawah grafik
    fig.text(0.5, -0.02, 
             'Gambar 1. Grafik Tren Aktivitas Komentar Publik di YouTube terkait Isu Dana Rp 200 Triliun',
             ha='center', fontsize=13, style='italic', wrap=True)
    
    plt.tight_layout()
    plt.savefig('grafik_tren_komentar.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print(f"\nGrafik berhasil dibuat!")
    print(f"Total hari: {len(daily_counts)}")
    print(f"Periode: {daily_counts['date'].min().date()} s/d {daily_counts['date'].max().date()}")
    print(f"Total komentar: {daily_counts['count'].sum()}")
    print(f"Rata-rata komentar per hari: {daily_counts['count'].mean():.2f}")
    print(f"\nGrafik disimpan sebagai: grafik_tren_komentar.png")
    
else:
    print("\nPERINGATAN: Tidak ditemukan kolom tanggal!")
    print("Dataset tidak memiliki informasi waktu, sehingga grafik tren tidak bisa dibuat.")
    print("\nSolusi:")
    print("1. Gunakan dataset_raw.csv atau dataset_filtered.csv yang masih punya kolom tanggal")
    print("2. Atau scraping ulang dengan menyimpan informasi publishedAt dari YouTube API")
