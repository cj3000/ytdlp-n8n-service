from flask import Flask, request, jsonify
import subprocess
import json

app = Flask(__name__)

@app.get("/")
def health():
    return {"status": "ok"}

@app.post("/playlist")
def playlist():
    url = request.json["url"]

    result = subprocess.check_output([
        "yt-dlp",
        "--flat-playlist",
        "--dump-json",
        url
    ]).decode("utf-8")

    videos = []

    for line in result.split("\n"):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
            vid = data.get("id")

            if not vid:
                continue

            videos.append({
                "id": vid,
                "title": data.get("title"),
                "url": f"https://www.youtube.com/watch?v={vid}"
            })

        except:
            pass

    return jsonify(videos)

@app.post("/download")
def download():
    url = request.json["url"]

    subprocess.Popen([
        "yt-dlp",
        "-o",
        "/downloads/%(title)s.%(ext)s",
        url
    ])

    return {"status": "started"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

from flask import send_from_directory
import os

DOWNLOAD_DIR = "/downloads"

@app.route("/files/<filename>")
def files(filename):
    return send_from_directory(DOWNLOAD_DIR, filename)

@app.route("/files")
def list_files():
    return {
        "files": os.listdir("/downloads")
    }
