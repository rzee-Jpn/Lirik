import os
import json
from bs4 import BeautifulSoup
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM

# ==== MODEL HF ====
MODEL_NAME = "google/flan-t5-base"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
parser = pipeline("text2text-generation", model=model, tokenizer=tokenizer)

# ==== FOLDER ====
INPUT_FOLDER = "data_raw"
OUTPUT_FOLDER = "data_clean"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ==== EXTRACT TEKS DARI HTML ====
def extract_text_from_html(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    return soup.get_text(separator="\n", strip=True)

# ==== PARSING KE STRUKTUR JSON ====
def parse_to_json(text):
    prompt = f"""
    Ekstrak dan rapikan data berikut dalam format JSON:
    - nama_artis
    - nama_panggung
    - tanggal_lahir
    - asal
    - media_sosial
    - album (daftar)
    - single (daftar)
    - label
    - pembuat_lirik
    - composer
    - arranger
    Jika data tidak ditemukan, kosongkan nilainya.

    Teks sumber:
    {text[:1500]}
    """
    result = parser(prompt, max_new_tokens=512, truncation=True)
    return result[0]['generated_text']

# ==== PROSES SEMUA FILE ====
for file_name in os.listdir(INPUT_FOLDER):
    if not file_name.endswith(".html"):
        continue

    print(f"📄 Memproses: {file_name}")
    text = extract_text_from_html(os.path.join(INPUT_FOLDER, file_name))

    try:
        parsed_json = parse_to_json(text)

        # Coba ubah ke JSON valid
        try:
            data = json.loads(parsed_json)
        except json.JSONDecodeError:
            data = {"raw_text": parsed_json}

        # Simpan hasil
        out_path = os.path.join(OUTPUT_FOLDER, file_name.replace(".html", ".json"))
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ Disimpan ke {out_path}")

    except Exception as e:
        print(f"❌ Gagal parsing {file_name}: {e}")