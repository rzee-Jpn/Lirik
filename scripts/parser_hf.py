import os
import json
import requests
from bs4 import BeautifulSoup

HF_TOKEN = os.getenv("HF_TOKEN")
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}
API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-small"  # model ringan gratis

RAW_DIR = "data_raw"
OUTPUT_DIR = "data_clean"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def parse_html_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    
    text = soup.get_text(separator="\n", strip=True)
    
    payload = {"inputs": f"Extract song data from this HTML:\n{text}"}
    response = requests.post(API_URL, headers=HEADERS, json=payload)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Error {response.status_code} for {file_path}: {response.text}")
        return {"error": response.text}

for filename in os.listdir(RAW_DIR):
    if filename.endswith(".html"):
        file_path = os.path.join(RAW_DIR, filename)
        print(f"🔄 Processing {filename}...")
        result = parse_html_file(file_path)
        
        output_file = os.path.join(OUTPUT_DIR, f"{os.path.splitext(filename)[0]}.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(f"✅ Saved → {output_file}")
