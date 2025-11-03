# parser_hf.py
import os
import json
from bs4 import BeautifulSoup
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline

# Konfigurasi model HF (gratis)
MODEL_NAME = "google/flan-t5-small"  # model ringan, cocok untuk teks
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

# Pipeline summarization / parsing
nlp = pipeline("text2text-generation", model=model, tokenizer=tokenizer)

# Folder input/output
INPUT_FOLDER = "data_raw"
OUTPUT_FOLDER = "data_clean"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Fungsi untuk ekstrak teks dari HTML
def extract_text_from_html(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    return soup.get_text(separator="\n", strip=True)

# Fungsi untuk parsing dengan HF
def parse_text(text):
    # Contoh: summarization / simplification
    result = nlp(text, max_length=512, truncation=True)
    return result[0]['generated_text']

# Proses semua file di folder
all_files = [f for f in os.listdir(INPUT_FOLDER) if f.endswith(".html")]

for file_name in all_files:
    print(f"Processing {file_name}...")
    text = extract_text_from_html(os.path.join(INPUT_FOLDER, file_name))
    
    # Bagi text menjadi batch jika terlalu panjang
    batch_size = 1000  # karakter per batch
    parsed_batches = []
    for i in range(0, len(text), batch_size):
        batch_text = text[i:i+batch_size]
        parsed = parse_text(batch_text)
        parsed_batches.append(parsed)
    
    # Gabungkan hasil
    parsed_text = "\n".join(parsed_batches)
    
    # Simpan hasil
    out_path = os.path.join(OUTPUT_FOLDER, file_name.replace(".html", ".json"))
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"parsed_text": parsed_text}, f, ensure_ascii=False, indent=2)

    print(f"Saved → {out_path}")