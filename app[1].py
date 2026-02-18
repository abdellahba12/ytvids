import os
import re
import uuid
import threading
from flask import Flask, render_template, request, jsonify, send_file, after_this_request
import yt_dlp

app = Flask(__name__)

DOWNLOAD_FOLDER = "/tmp/yt_downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Track download progress per job
jobs = {}

def sanitize_filename(name):
    return re.sub(r'[^\w\s\-.]', '', name).strip()


def download_video(job_id, url, format_choice, quality):
    jobs[job_id] = {"status": "downloading", "progress": 0, "filename": None, "error": None}

    def progress_hook(d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            downloaded = d.get("downloaded_bytes", 0)
            if total:
                jobs[job_id]["progress"] = round(downloaded / total * 100, 1)
        elif d["status"] == "finished":
            jobs[job_id]["progress"] = 100

    output_template = os.path.join(DOWNLOAD_FOLDER, f"{job_id}_%(title)s.%(ext)s")

    if format_choice == "audio":
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_template,
            "progress_hooks": [progress_hook],
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "quiet": True,
        }
    else:
        fmt = f"bestvideo[height<={quality}]+bestaudio/best[height<={quality}]" if quality != "best" else "bestvideo+bestaudio/best"
        ydl_opts = {
            "format": fmt,
            "outtmpl": output_template,
            "progress_hooks": [progress_hook],
            "merge_output_format": "mp4",
            "quiet": True,
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = sanitize_filename(info.get("title", "video"))

        # Find downloaded file
        for f in os.listdir(DOWNLOAD_FOLDER):
            if f.startswith(job_id):
                jobs[job_id]["filename"] = f
                jobs[job_id]["title"] = title
                break

        jobs[job_id]["status"] = "done"
    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/info", methods=["POST"])
def get_info():
    url = request.json.get("url", "").strip()
    if not url:
        return jsonify({"error": "URL requerida"}), 400
    try:
        with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
            info = ydl.extract_info(url, download=False)
        return jsonify({
            "title": info.get("title"),
            "duration": info.get("duration"),
            "thumbnail": info.get("thumbnail"),
            "uploader": info.get("uploader"),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/download", methods=["POST"])
def start_download():
    data = request.json
    url = data.get("url", "").strip()
    format_choice = data.get("format", "video")  # video or audio
    quality = data.get("quality", "1080")

    if not url:
        return jsonify({"error": "URL requerida"}), 400

    job_id = str(uuid.uuid4())[:8]
    thread = threading.Thread(target=download_video, args=(job_id, url, format_choice, quality))
    thread.daemon = True
    thread.start()

    return jsonify({"job_id": job_id})


@app.route("/api/status/<job_id>")
def check_status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job no encontrado"}), 404
    return jsonify(job)


@app.route("/api/file/<job_id>")
def get_file(job_id):
    job = jobs.get(job_id)
    if not job or job["status"] != "done" or not job.get("filename"):
        return jsonify({"error": "Archivo no disponible"}), 404

    filepath = os.path.join(DOWNLOAD_FOLDER, job["filename"])
    if not os.path.exists(filepath):
        return jsonify({"error": "Archivo no encontrado"}), 404

    @after_this_request
    def cleanup(response):
        def remove_file():
            try:
                os.remove(filepath)
                del jobs[job_id]
            except Exception:
                pass
        threading.Timer(30, remove_file).start()
        return response

    return send_file(filepath, as_attachment=True, download_name=job["filename"].replace(f"{job_id}_", ""))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
