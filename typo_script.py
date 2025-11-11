import os
import re
import time
import json
import pandas as pd
import ast
from google import genai
from dotenv import load_dotenv

# Inisialisasi koneksi ke Gemini API
load_dotenv(override=True)
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_KEY:
    raise RuntimeError("GEMINI_API_KEY tidak ditemukan di environment variables")

client = genai.Client(api_key=GEMINI_KEY)

# Fungsi untuk deteksi dan koreksi typo
def check_typo_batch(comments):
    numbered_comments = "\n".join([f"{i+1}. {c}" for i, c in enumerate(comments)])

    prompt = f"""
    Anda adalah asisten bahasa Indonesia yang bertugas mendeteksi dan memperbaiki kesalahan ejaan (typo) dalam teks.
    Baca dengan teliti setiap komentar berikut dan berikan daftar kata yang salah eja beserta perbaikannya. Tolong jangan mengubah arti katanya.
    Semua output harus dalam bahasa Indonesia. Jika ada kata yang benar ejaannya, jangan sertakan dalam output.
    kata_benar tidak boleh memiliki huruf kapital, semuanya harus dalam huruf kecil.

    Jumlah komentar ada {len(comments)}.
    Jika tidak ditemukan typo pada komentar, lewati komentar tersebut.

    Berikut daftar komentar yang perlu diperiksa:
    {numbered_comments}

    Kembalikan hasil dalam format dictionary Python yang valid.
    Setiap pasangan harus ditulis dengan tanda kutip ganda (") seperti contoh berikut:
    {{
    "kata_salah1": "kata_benar1",
    "kata_salah2": "kata_benar2"
    }}

    JANGAN tulis koma di akhir dictionary.
    Pastikan semua key dan value adalah string berhuruf kecil.
    Jika tidak ada typo sama sekali, kembalikan dictionary kosong.
    Hanya berikan dictionary saja tanpa teks tambahan, tanpa ```python, tanpa penjelasan, tanpa komentar.
    """

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )

    raw_output = response.text.strip()

    # Bersihkan tanda ``` jika muncul
    raw_output = re.sub(r"^```(?:python)?", "", raw_output)
    raw_output = re.sub(r"```$", "", raw_output).strip()

    # Parsing hasil secara aman dengan literal_eval
    try:
        typo_dict = ast.literal_eval(raw_output)
        if isinstance(typo_dict, dict):
            # hilangkan kapitalisasi, spasi, dan entri duplikat
            typo_dict = {
                k.strip(): v.strip().lower()
                for k, v in typo_dict.items()
                if isinstance(k, str)
                and isinstance(v, str)
                and k.strip()
                and v.strip()
                and k.lower() != v.lower()  # pastikan tidak sama
            }
            return typo_dict
        else:
            print("Output bukan dictionary, hasil mentah:")
            print(raw_output)
            return {}
    except Exception:
        print("Format output tidak valid, hasil mentah:")
        print(raw_output)
        return {}

# Fungsi proses deteksi typo dari tiap batch komentar
def process_typo_detection(df, client, batch_size=10, delay=30):
    all_typos = {}

    for i in range(0, len(df), batch_size):
        batch_comments = df['comment'].iloc[i:i+batch_size].astype(str).tolist()
        print(f"\nMemproses batch {i//batch_size + 1} ({len(batch_comments)} komentar)...")

        while True:
            try:
                typo_dict = check_typo_batch(batch_comments)

                # Validasi apakah hasil dictionary valid
                if not isinstance(typo_dict, dict) or len(typo_dict) == 0:
                    print(f"Format output tidak valid atau kosong pada batch {i//batch_size + 1}. Mengulang setelah {delay} detik...")
                    time.sleep(delay)
                    continue

                break

            except Exception as e:
                if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
                    print("Terkena limit API (429). Menunggu 120 detik sebelum mencoba ulang batch ini...")
                    time.sleep(120)
                else:
                    print(f"Terjadi error pada batch {i//batch_size + 1}: {e}")
                    print(f"Mengulang batch ini setelah {delay} detik...")
                    time.sleep(delay)
                continue  # Ulangi batch jika ada error

        all_typos.update(typo_dict)

        if i + batch_size < len(df):
            print(f"Menunggu {delay} detik sebelum lanjut ke batch berikutnya.")
            time.sleep(delay)

    return all_typos

input_csv = "dataset_filtered.csv"
output_json = "typo_dict.json"

print(f"Membaca file: {input_csv}")
df = pd.read_csv(input_csv)
df = df[['comment']].copy()

typo_dict = process_typo_detection(df, client, batch_size=50, delay=30)

with open(output_json, "w", encoding="utf-8") as f:
    json.dump(typo_dict, f, ensure_ascii=False, indent=2)

print(f"\nDeteksi typo selesai. Hasil disimpan ke: {output_json}")