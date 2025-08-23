# credits: chatgpt
# just for an example in main.py
from pathlib import Path
import requests

def download_image(url, dest_dir="downloads", n=1):
    p = Path(dest_dir) / f"image{n}{Path(url).suffix}"
    p.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True) as r, open(p, "wb") as f:
        for chunk in r.iter_content(8192):
            if chunk: f.write(chunk)
    return str(p)
