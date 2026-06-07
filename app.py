from flask import Flask, request, jsonify, send_from_directory, render_template
import os
import yt_dlp

app = Flask(__name__)

DOWNLOAD_DIR = "/downloads"
VIDEO_DIR = f"{DOWNLOAD_DIR}/videos"
THUMBNAIL_DIR = f"{DOWNLOAD_DIR}/thumbnails"

os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(THUMBNAIL_DIR, exist_ok=True)

COOKIE_FILE = "/app/www.youtube.com_cookies.txt"  

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# -------------------------
# HELPERS (UTIL FUNCTIONS)
# -------------------------

def download_thumbnail(video_id):
    os.makedirs(f"{DOWNLOAD_DIR}/thumbnails", exist_ok=True)

    url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
    path = f"{DOWNLOAD_DIR}/thumbnails/{video_id}.jpg"

    r = requests.get(url, stream=True)
    if r.status_code == 200:
        with open(path, "wb") as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)

    return path

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
            "url": f"https://www.youtube.com/watch?v={e.get('id')}",
            "thumbnail": f"https://img.youtube.com/vi/{e.get('id')}/hqdefault.jpg"
        })

    return jsonify(entries)


# -------------------------
# DASHBOARD
# -------------------------
import psycopg2

@app.route("/dashboard")
def dashboard():

    conn = psycopg2.connect(
        host="nocodb_youtube_db",
        database="postgres",
        user="postgres",
        password="jpb4jp24r9ppvyi49rrg"
    )

    cur = conn.cursor()

    cur.execute("""
        SELECT
            video_id,
            title,
            url,
            thumbnail,
            watched
        FROM youtube_videos
        ORDER BY created_at DESC
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    videos = []

    for row in rows:
        videos.append({
            "video_id": row[0],
            "title": row[1],
            "url": row[2],
            "thumbnail": row[3],
            "watched": row[4]
        })

    return render_template(
        "dashboard.html",
        videos=videos
    )


# -------------------------
# DOWNLOAD
# -------------------------
@app.route("/download", methods=["POST"])
def download():
    data = request.get_json()
    url = data.get("url")

    if not url:
        return jsonify({"error": "missing url"}), 400

    video_id = url.split("v=")[-1]

    video_path = f"/downloads/videos/{video_id}.mp4"
    thumb_path = f"/downloads/thumbnails/{video_id}.jpg"

  ydl_opts = {
        "outtmpl": f"{VIDEO_DIR}/%(id)s.%(ext)s",
        "format": "best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    download_thumbnail(video_id)

    # DB update
    conn = psycopg2.connect(...)
    cur = conn.cursor()

    cur.execute("""
        UPDATE youtube_videos
        SET local_video_path = %s,
            local_thumbnail_path = %s,
            download_status = 'done'
        WHERE video_id = %s
    """, (video_path, thumb_path, video_id))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({
        "status": "success",
        "video_id": video_id,
        "file": video_path
    })

# -------------------------
# FILE SERVER (WICHTIG)
# -------------------------
@app.route("/files/<path:filename>", methods=["GET"])
def files(filename):
    return send_from_directory(DOWNLOAD_DIR, filename, as_attachment=False)


# -------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
