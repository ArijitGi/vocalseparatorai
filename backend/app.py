import os
import uuid
import subprocess
import yt_dlp
import threading
import time
import sys
import zipfile
from io import BytesIO
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__)

# Configure CORS properly
CORS(app, resources={
    r"/api/*": {
        "origins": ["*"],  # Allow all origins for testing
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["*"]
    }
})

# Create necessary directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
SEPARATED_FOLDER = os.path.join(BASE_DIR, "separated")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SEPARATED_FOLDER, exist_ok=True)

MODEL = "htdemucs_ft"

# Global status tracking
progress_status = {}
start_times = {}
job_file_mapping = {}

# Test route to verify deployment
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "running",
        "message": "Vocal Separator API is running",
        "endpoints": [
            "/api/health",
            "/api/upload",
            "/api/youtube",
            "/api/progress/<job_id>",
            "/api/result/<job_id>"
        ]
    })

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "timestamp": time.time()})

def run_demucs_background(filepath, job_id, original_filename=None):
    try:
        print(f"JOB START: {job_id}")
        print(f"Filepath: {filepath}")
        
        start_times[job_id] = time.time()
        progress_status[job_id] = 5
        
        filepath = os.path.abspath(filepath)
        filename_without_ext = os.path.splitext(os.path.basename(filepath))[0]
        
        print(f"Processing file: {filename_without_ext}")
        
        # Run demucs
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "demucs",
                "-n", MODEL,
                "--two-stems", "vocals",
                filepath
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Monitor progress
        while process.poll() is None:
            if process.stdout:
                line = process.stdout.readline()
                if line:
                    print(line.strip())
            time.sleep(1)
        
        process.wait()
        print(f"Process finished with return code: {process.returncode}")
        
        # Find output folder
        result_folder = os.path.join(SEPARATED_FOLDER, MODEL, filename_without_ext)
        
        if not os.path.exists(result_folder):
            model_path = os.path.join(SEPARATED_FOLDER, MODEL)
            if os.path.exists(model_path):
                for folder in os.listdir(model_path):
                    if filename_without_ext in folder:
                        result_folder = os.path.join(SEPARATED_FOLDER, MODEL, folder)
                        break
        
        vocals = os.path.join(result_folder, "vocals.wav")
        print(f"Looking for vocals at: {vocals}")
        
        wait_count = 0
        while not os.path.exists(vocals) and wait_count < 600:
            time.sleep(1)
            wait_count += 1
        
        if os.path.exists(vocals):
            print(f"Found vocals at: {vocals}")
            progress_status[job_id] = 100
        else:
            print(f"TIMEOUT: vocals not found")
            progress_status[job_id] = 0
            
    except Exception as e:
        print(f"ERROR in demucs: {e}")
        import traceback
        traceback.print_exc()
        progress_status[job_id] = 0

@app.route("/api/upload", methods=["POST", "OPTIONS"])
def upload():
    if request.method == "OPTIONS":
        return jsonify({}), 200
    
    try:
        file = request.files.get("file")
        if not file:
            return jsonify({"error": "No file provided"}), 400
        
        job_id = str(uuid.uuid4())
        original_name = os.path.splitext(file.filename)[0]
        original_name = "".join(c for c in original_name if c.isalnum() or c in (' ', '-', '_')).replace(' ', '_')
        
        filename = f"{original_name}_{job_id}.mp3"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        job_file_mapping[job_id] = original_name
        
        print(f"Job {job_id}: File saved to {filepath}")
        
        thread = threading.Thread(
            target=run_demucs_background,
            args=(filepath, job_id),
            daemon=True
        )
        thread.start()
        
        return jsonify({"job_id": job_id})
        
    except Exception as e:
        print(f"Upload error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/youtube", methods=["POST", "OPTIONS"])
def youtube():
    if request.method == "OPTIONS":
        return jsonify({}), 200
    
    try:
        url = request.json.get("url")
        if not url:
            return jsonify({"error": "No URL provided"}), 400
        
        job_id = str(uuid.uuid4())
        progress_status[job_id] = 10
        start_times[job_id] = time.time()
        
        output_template = os.path.join(UPLOAD_FOLDER, f"{job_id}.%(ext)s")
        
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_template,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "320"
            }],
            "quiet": False,
            "noplaylist": True,
        }
        
        print(f"Downloading: {url}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', job_id)
            title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).replace(' ', '_')
        
        progress_status[job_id] = 15
        
        filepath = os.path.join(UPLOAD_FOLDER, f"{job_id}.mp3")
        
        if not os.path.exists(filepath):
            files = os.listdir(UPLOAD_FOLDER)
            for f in files:
                if job_id in f and f.endswith('.mp3'):
                    filepath = os.path.join(UPLOAD_FOLDER, f)
                    break
        
        if not os.path.exists(filepath):
            return jsonify({"error": "Download failed"}), 500
        
        job_file_mapping[job_id] = title
        
        thread = threading.Thread(
            target=run_demucs_background,
            args=(filepath, job_id),
            daemon=True
        )
        thread.start()
        
        return jsonify({"job_id": job_id})
        
    except Exception as e:
        print(f"YouTube error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/progress/<job_id>", methods=["GET"])
def progress(job_id):
    progress = progress_status.get(job_id, 0)
    elapsed = int(time.time() - start_times.get(job_id, time.time())) if job_id in start_times else 0
    
    return jsonify({
        "progress": progress,
        "elapsed": elapsed,
        "estimate": 300
    })

@app.route("/api/result/<job_id>", methods=["GET"])
def result(job_id):
    try:
        original_name = job_file_mapping.get(job_id)
        
        if original_name:
            result_folder = os.path.join(SEPARATED_FOLDER, MODEL, original_name)
            if not os.path.exists(result_folder):
                # Try with job_id appended
                alt_folder = os.path.join(SEPARATED_FOLDER, MODEL, f"{original_name}_{job_id}")
                if os.path.exists(alt_folder):
                    result_folder = alt_folder
        
        if not os.path.exists(result_folder):
            # Search by job_id
            model_path = os.path.join(SEPARATED_FOLDER, MODEL)
            if os.path.exists(model_path):
                for folder in os.listdir(model_path):
                    if job_id in folder:
                        result_folder = os.path.join(SEPARATED_FOLDER, MODEL, folder)
                        break
        
        if not os.path.exists(result_folder):
            return jsonify({"status": "processing"})
        
        vocals = os.path.join(result_folder, "vocals.wav")
        instrumental = os.path.join(result_folder, "no_vocals.wav")
        
        if not os.path.exists(vocals):
            return jsonify({"status": "processing"})
        
        base_url = request.host_url.rstrip('/')
        
        return jsonify({
            "status": "done",
            "vocals": f"{base_url}/api/download?file={vocals}",
            "instrumental": f"{base_url}/api/download?file={instrumental}",
            "zip": f"{base_url}/api/download_zip/{job_id}"
        })
        
    except Exception as e:
        print(f"Result error: {e}")
        return jsonify({"status": "error", "message": str(e)})

@app.route("/api/download_zip/<job_id>", methods=["GET"])
def download_zip(job_id):
    try:
        result_folder = None
        original_name = job_file_mapping.get(job_id)
        
        if original_name:
            folder_path = os.path.join(SEPARATED_FOLDER, MODEL, original_name)
            if os.path.exists(folder_path):
                result_folder = folder_path
        
        if not result_folder:
            model_path = os.path.join(SEPARATED_FOLDER, MODEL)
            if os.path.exists(model_path):
                for folder in os.listdir(model_path):
                    if job_id in folder:
                        result_folder = os.path.join(SEPARATED_FOLDER, MODEL, folder)
                        break
        
        if not result_folder:
            return "Result not ready", 404
        
        vocals = os.path.join(result_folder, "vocals.wav")
        instrumental = os.path.join(result_folder, "no_vocals.wav")
        
        if not os.path.exists(vocals):
            return "Not ready", 404
        
        memory_file = BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as z:
            z.write(vocals, "vocals.wav")
            z.write(instrumental, "instrumental.wav")
        
        memory_file.seek(0)
        
        return send_file(
            memory_file,
            download_name="separated_tracks.zip",
            as_attachment=True,
            mimetype="application/zip"
        )
        
    except Exception as e:
        print(f"Zip download error: {e}")
        return str(e), 500

@app.route("/api/download", methods=["GET"])
def download():
    try:
        file_path = request.args.get("file")
        if not file_path or not os.path.exists(file_path):
            return "File not found", 404
        
        return send_file(
            file_path,
            mimetype="audio/wav",
            as_attachment=False
        )
        
    except Exception as e:
        print(f"Download error: {e}")
        return str(e), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)