# lyrics-datalake-repo

Auto-parse local files in `datalake/` and merge into `artists/*.json`.

## Run locally

1. python -m venv venv
2. source venv/bin/activate
3. pip install -r requirements.txt
4. python -m scripts.main

## Workflow
- Drop files into `datalake/`.
- Run `scripts/main.py` to update `artists/`.
- Use `artists/{artist}.json` via CDN (jsDelivr) in Blogger.
