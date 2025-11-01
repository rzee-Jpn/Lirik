# utils.py
import os
import json
import re
from slugify import slugify
from datetime import datetime

UTF8 = 'utf-8'

FIELD_SYNONYMS = {
    'title': ['title', 'judul', 'song', 'track'],
    'artist': ['artist', 'artis', 'penyanyi', 'band'],
    'album': ['album'],
    'release_date': ['release_date', 'rilis', 'released'],
    'lyrics': ['lyrics', 'lirik'],
    'writer': ['writer', 'penulis', 'songwriter']
}


def now_iso():
    return datetime.utcnow().isoformat() + 'Z'


def safe_slug(s):
    if not s:
        return 'unknown'
    return slugify(s, lowercase=True)


def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding=UTF8) as f:
        return json.load(f)


def save_json(path, data):
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)
    with open(path, 'w', encoding=UTF8) as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def guess_artist_from_filename(fname):
    # heuristic: artist_title_lang.ext or artist-title.ext
    base = os.path.splitext(os.path.basename(fname))[0]
    parts = re.split(r'[_\-–]', base)
    if len(parts) >= 2:
        return parts[0].strip()
    return 'unknown'
