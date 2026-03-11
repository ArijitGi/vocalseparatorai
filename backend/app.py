import os
import uuid
import subprocess
import yt_dlp
import threading
import time
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

UPLOAD_FOLDER = "uploads"
SEPARATED_FOLDER = "separated"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SEPARATED_FOLDER, exist_ok=True)

app = Flask(__name__)
CORS(
    app,
    resources={r"/api/*": {"origins": "*"}},
    supports_credentials=True
)

BASE_DIR = os.getcwd()
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
SEPARATED_FOLDER = os.path.join(BASE_DIR, "separated")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SEPARATED_FOLDER, exist_ok=True)

FFMPEG_BIN_PATH = ""

progress_status = {}


def run_demucs_background(filepath, unique_name):

    progress_status[unique_name] = {
        "progress": 0,
        "status": "processing"
    }

    process = subprocess.Popen(
        [
            "python",
            "-m",
            "demucs",
            "-n","mdx_q",
            "--segment","8",
            filepath
        ]
    )

    while process.poll() is None:

        current = progress_status[unique_name]["progress"]

        if current < 90:
            progress_status[unique_name]["progress"] += 2

        time.sleep(5)

    process.wait()

    filename = os.path.basename(filepath)

    result_folder = os.path.join(
        SEPARATED_FOLDER,
        "mdx_q",
        filename
    )

    vocals = os.path.join(result_folder,"vocals.wav")

    while not os.path.exists(vocals):
        time.sleep(2)

    progress_status[unique_name] = {
        "progress":100,
        "status":"done"
    }

# ---------------- API ROUTES ----------------

@app.route("/api/upload", methods=["POST"])
def upload():
    file = request.files.get("file")

    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    unique_name = str(uuid.uuid4())
    filepath = os.path.join(UPLOAD_FOLDER, unique_name + ".mp3")
    file.save(filepath)

    thread = threading.Thread(
        target=run_demucs_background,
        args=(filepath, unique_name)
    )
    thread.start()

    return jsonify({"job_id": unique_name})


@app.route("/api/youtube", methods=["POST"])
def youtube_download():
    data = request.json
    url = data.get("url")

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    unique_name = str(uuid.uuid4())
    output_path = os.path.join(UPLOAD_FOLDER, unique_name)

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'ffmpeg_location': FFMPEG_BIN_PATH
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    filepath = output_path + ".mp3"

    thread = threading.Thread(
        target=run_demucs_background,
        args=(filepath, unique_name)
    )
    thread.start()

    return jsonify({"job_id": unique_name})


@app.route("/api/progress/<job_id>")
def progress(job_id):

    job = progress_status.get(job_id)

    if not job:
        return jsonify({
            "progress":0,
            "status":"waiting"
        })

    return jsonify(job)

@app.route("/api/result/<job_id>")
def result(job_id):

    result_folder = os.path.join(
    SEPARATED_FOLDER,
    "mdx_q",
    job_id + ".mp3"
)

    vocals_path = os.path.join(result_folder, "vocals.wav")
    drums_path = os.path.join(result_folder, "drums.wav")
    bass_path = os.path.join(result_folder, "bass.wav")
    other_path = os.path.join(result_folder, "other.wav")

    if not os.path.exists(vocals_path):
        return jsonify({"status": "processing"})

    base_url = request.host_url

    return jsonify({
        "status": "done",
        "vocals": f"{base_url}api/download?file={vocals_path}",
        "drums": f"{base_url}api/download?file={drums_path}",
        "bass": f"{base_url}api/download?file={bass_path}",
        "other": f"{base_url}api/download?file={other_path}"
    })

@app.route("/api/download")
def download():
    file_path = request.args.get("file")

    if not file_path or not os.path.exists(file_path):
        return "File not found", 404

    return send_file(file_path, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)