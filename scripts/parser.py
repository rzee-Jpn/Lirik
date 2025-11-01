# parser.py
import csv
from bs4 import BeautifulSoup
from scripts.utils import guess_artist_from_filename


def parse_txt(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = [l.rstrip() for l in f.readlines() if l.strip()]
    if not lines:
        return {}
    # heuristic: first non-empty line title if contains - or by position
    title = lines[0]
    body = '\n'.join(lines[1:]) if len(lines) > 1 else ''
    return {
        'title': title,
        'lyrics': body,
        'source_file': path
    }


def parse_csv(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if not rows:
        return {}
    r = rows[0]
    return {
        'title': r.get('title') or r.get('judul') or '',
        'artist': r.get('artist') or r.get('artis') or '',
        'album': r.get('album') or '',
        'release_date': r.get('release_date') or r.get('rilis') or '',
        'lyrics': r.get('lyrics') or r.get('lirik') or ''
    }


def parse_html(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        html = f.read()
    soup = BeautifulSoup(html, 'lxml')
    title = ''
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    # try to get meta property=og:title
    og = soup.find('meta', property='og:title')
    if og and og.get('content'):
        title = og.get('content')
    text = soup.get_text(separator='\n')
    return {
        'title': title,
        'lyrics': text,
        'source_file': path
  }
