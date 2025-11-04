import os
import json
from groq import Groq

# Pastikan kamu sudah set environment variable:
# GROQ_API_KEY = "key_anda_dari_console.groq.com"

RAW_DIR = "data_raw"
OUTPUT_DIR = "data_clean"

os.makedirs(OUTPUT_DIR, exist_ok=True)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

TEMPLATE_PROMPT = """
Kamu adalah parser musik profesional.
Tugasmu adalah membaca teks deskripsi lagu atau artis di bawah ini dan mengubahnya
menjadi JSON dengan format seperti berikut (jangan ubah struktur kunci):

{
  "Bio / Profil": {
    "Nama lengkap & nama panggung": "",
    "Asal / domisili": "",
    "Tanggal lahir": "",
    "Genre musik": "",
    "Influences / inspirasi": "",
    "Cerita perjalanan musik": "",
    "Foto profil": "",
    "Link media sosial": {
      "BandLab": "",
      "YouTube": "",
      "Spotify": "",
      "Instagram": ""
    }
  },
  "Diskografi": [
    {
      "Nama album/single": "",
      "Tanggal rilis": "",
      "Label": "",
      "Jumlah lagu": "",
      "Cover art": "",
      "Produksi oleh / kolaborator tetap": "",
      "Lagu / Song List": [
        {
          "Judul lagu": "",
          "Composer": "",
          "Lyricist": "",
          "Featuring": "",
          "Tahun rilis": "",
          "Album asal": "",
          "Durasi": "",
          "Genre": "",
          "Key": "",
          "Chord & lyrics": "",
          "Terjemahan": ""
        }
      ]
    }
  ]
}

Instruksi tambahan:
- Pastikan output berupa **JSON valid**.
- Abaikan judul anime, film, atau serial TV (hanya fokus pada lagu dan albumnya).
- Jika data tidak ditemukan, biarkan nilai string kosong.
- Ambil semua info yang ada di teks (judul, durasi, kolaborator, label, dll).
"""

def parse_with_groq(text: str):
    response = client.chat.completions.create(
        model="mixtral-8x7b-32768",
        temperature=0.2,
        messages=[
            {"role": "system", "content": "Kamu harus selalu output JSON valid dan lengkap."},
            {"role": "user", "content": TEMPLATE_PROMPT + "\n\nTeks:\n" + text}
        ]
    )

    content = response.choices[0].message.content.strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        print("⚠️ JSON invalid, mencoba perbaikan sederhana...")
        # Coba bersihkan teks
        fixed = content[content.find("{") : content.rfind("}") + 1]
        try:
            return json.loads(fixed)
        except Exception:
            print("❌ Tidak bisa parse JSON.")
            return {"error": "Invalid JSON", "raw": content}


def main():
    for file in os.listdir(RAW_DIR):
        if not file.endswith(".txt"):
            continue

        raw_path = os.path.join(RAW_DIR, file)
        out_path = os.path.join(OUTPUT_DIR, file.replace(".txt", ".json"))

        print(f"🧠 Memproses: {file} ...")
        with open(raw_path, "r", encoding="utf-8") as f:
            raw_text = f.read().strip()

        parsed = parse_with_groq(raw_text)

        with open(out_path, "w", encoding="utf-8") as out:
            json.dump({"raw_text": raw_text, "parsed_info": parsed}, out, indent=2, ensure_ascii=False)

        print(f"✅ Disimpan ke {out_path}\n")


if __name__ == "__main__":
    main()