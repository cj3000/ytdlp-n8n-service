from flask import Flask, request, jsonify, send_from_directory
import os
import yt_dlp

app = Flask(__name__)

DOWNLOAD_DIR = "/downloads"
COOKIE_FILE = "/app/www.youtube.com_cookies.txt"  

os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# -------------------------
# HEALTH CHECK
# -------------------------
@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


# -------------------------
# PLAYLIST
# -------------------------
@app.route("/playlist", methods=["POST"])
def playlist():
    data = request.get_json(silent=True)

    if not data or "url" not in data:
        return jsonify({"error": "missing url"}), 400

    url = data["url"]

    ydl_opts = {
        "quiet": True,
        "extract_flat": True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    entries = []
    for e in info.get("entries", []):
        entries.append({
            "id": e.get("id"),
            "title": e.get("title"),
            "url": f"https://www.youtube.com/watch?v={e.get('id')}"
            "thumbnail": f"https://img.youtube.com/vi/{e.get('id')}/hqdefault.jpg"
        })

    return jsonify(entries)


# -------------------------
# DOWNLOAD
# -------------------------
@app.route("/download", methods=["POST"])
def download():
    data = request.get_json()
    url = data.get("url")

    if not url:
        return jsonify({"error": "missing url"}), 400

    ydl_opts = {
        "outtmpl": f"{DOWNLOAD_DIR}/%(title)s.%(ext)s",
        "format": "best[ext=mp4]/best",
        "noplaylist": True,
        "quiet": True
    }

 

    if os.path.exists(COOKIE_FILE):
       print("COOKIE FILE FOUND:", COOKIE_FILE)
       ydl_opts["cookiefile"] = COOKIE_FILE
    else:
       print("COOKIE FILE NOT FOUND:", COOKIE_FILE)

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    filename = ydl.prepare_filename(info)

    return jsonify({
        "status": "success",
        "file": filename.split("/")[-1]
    })

ydl_opts = {
    "outtmpl": f"{DOWNLOAD_DIR}/%(title)s.%(ext)s",
    "format": "best[ext=mp4]/best",
    "noplaylist": True,
    "quiet": True,
}
if os.path.exists(COOKIE_FILE):
    ydl_opts["cookiefile"] = COOKIE_FILE

# -------------------------
# FILE SERVER (WICHTIG)
# -------------------------
@app.route("/files/<path:filename>", methods=["GET"])
def files(filename):
    return send_from_directory(DOWNLOAD_DIR, filename, as_attachment=False)


# -------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
