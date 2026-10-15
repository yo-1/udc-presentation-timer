from pathlib import Path
root=Path(__file__).resolve().parents[1]
for p in ["web/index.html","pwa/index.html","pwa/manifest.webmanifest","pwa/service-worker.js","windows/udc_timer.py","assets/bell.mp3"]:
 assert (root/p).is_file(),p
assert "n:4" in (root/"web/index.html").read_text(encoding="utf-8")
