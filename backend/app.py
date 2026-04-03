print("SERVER VERSION 4 - Cloudinary Integration")

import os
import uuid
import subprocess
import yt_dlp  # Fixed: added underscore
import threading
import time
import sys
import zipfile
import shutil
import tempfile
from io import BytesIO
from datetime import datetime, timedelta

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import cloudinary
import cloudinary.uploader
import cloudinary.utils

app = Flask(__name__)

# Configure CORS properly
CORS(app, resources={
    r"/api/*": {
        "origins": ["*"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["*"]
    }
})

# Configure Cloudinary (Add your credentials here)
# IMPORTANT: Set these as environment variables on Render for security
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME", "YOUR_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY", "YOUR_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET", "YOUR_API_SECRET"),
    secure=True
)

# Create necessary directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
SEPARATED_FOLDER = os.path.join(BASE_DIR, "separated")

# Create folders if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SEPARATED_FOLDER, exist_ok=True)

MODEL = "htdemucs"  # Lighter model to save memory

# Global status tracking
progress_status = {}
start_times = {}
job_results = {}  # Store Cloudinary URLs
job_file_mapping = {}

# Test route to verify deployment
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "running",
        "message": "Vocal Separator API is running with Cloudinary storage",
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

def cleanup_temp_files(filepath, result_folder=None):
    """Clean up temporary files immediately after processing"""
    try:
        # Delete original uploaded file
        if filepath and os.path.exists(filepath):
            os.unlink(filepath)
            print(f"Deleted upload file: {filepath}")
        
        # Delete separated folder if it exists
        if result_folder and os.path.exists(result_folder):
            shutil.rmtree(result_folder)
            print(f"Deleted result folder: {result_folder}")
            
    except Exception as e:
        print(f"Cleanup error: {e}")

def upload_to_cloudinary(file_path, public_id_prefix, resource_type="auto"):
    """Upload file to Cloudinary and return URL"""
    try:
        result = cloudinary.uploader.upload(
            file_path,
            resource_type=resource_type,
            public_id=f"vocalseparator/{public_id_prefix}_{int(time.time())}",
            folder="vocalseparatorai",
            overwrite=True
        )
        return result['secure_url']
    except Exception as e:
        print(f"Cloudinary upload error: {e}")
        return None

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
                    if "Separating" in line:
                        progress_status[job_id] = min(progress_status[job_id] + 10, 90)
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
        instrumental = os.path.join(result_folder, "no_vocals.wav")
        
        print(f"Looking for vocals at: {vocals}")
        
        wait_count = 0
        while not os.path.exists(vocals) and wait_count < 600:
            time.sleep(1)
            wait_count += 1
        
        if os.path.exists(vocals):
            print(f"Found vocals at: {vocals}")
            progress_status[job_id] = 95
            
            # Upload to Cloudinary
            print("Uploading vocals to Cloudinary...")
            vocals_url = upload_to_cloudinary(vocals, f"vocals_{job_id}", "auto")
            
            print("Uploading instrumental to Cloudinary...")
            instrumental_url = upload_to_cloudinary(instrumental, f"instrumental_{job_id}", "auto")
            
            if vocals_url and instrumental_url:
                job_results[job_id] = {
                    "vocals": vocals_url,
                    "instrumental": instrumental_url
                }
                progress_status[job_id] = 100
                print(f"JOB DONE: {job_id} - Files uploaded to Cloudinary")
            else:
                print("Failed to upload to Cloudinary")
                progress_status[job_id] = 0
            
            # Clean up immediately after upload
            cleanup_temp_files(filepath, result_folder)
            
        else:
            print(f"TIMEOUT: vocals not found")
            progress_status[job_id] = 0
            cleanup_temp_files(filepath, None)
        
    except Exception as e:
        print(f"ERROR in demucs: {e}")
        import traceback
        traceback.print_exc()
        progress_status[job_id] = 0
        cleanup_temp_files(filepath, None)

@app.route("/api/upload", methods=["POST", "OPTIONS"])
def upload():
    if request.method == "OPTIONS":
        return jsonify({}), 200
    
    try:
        file = request.files.get("file")
        if not file:
            return jsonify({"error": "No file provided"}), 400
        
        job_id = str(uuid.uuid4())
        
        # Save to temp file
        original_name = os.path.splitext(file.filename)[0]
        original_name = "".join(c for c in original_name if c.isalnum() or c in (' ', '-', '_')).replace(' ', '_')
        
        filename = f"{original_name}_{job_id}.mp3"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        job_file_mapping[job_id] = original_name
        
        print(f"Job {job_id}: File saved to {filepath}")
        
        # Start background processing
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
        
        # Create temporary file
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
        
        # Start background processing
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
        # Check if results are ready
        if job_id in job_results:
            return jsonify({
                "status": "done",
                "vocals": job_results[job_id]["vocals"],
                "instrumental": job_results[job_id]["instrumental"]
            })
        else:
            # Check if still processing
            progress = progress_status.get(job_id, 0)
            if progress == 100:
                # Should be in job_results, but just in case
                return jsonify({"status": "processing"})
            elif progress > 0:
                return jsonify({"status": "processing"})
            else:
                return jsonify({"status": "processing"})
        
    except Exception as e:
        print(f"Result error: {e}")
        return jsonify({"status": "error", "message": str(e)})

# Automatic cleanup job - runs every hour to clean old files
def scheduled_cleanup():
    """Delete files older than 1 hour"""
    while True:
        try:
            time.sleep(3600)  # Run every hour
            
            # Clean uploads folder
            for folder in [UPLOAD_FOLDER, SEPARATED_FOLDER]:
                if os.path.exists(folder):
                    for item in os.listdir(folder):
                        item_path = os.path.join(folder, item)
                        if os.path.isfile(item_path):
                            # Delete if older than 1 hour
                            if time.time() - os.path.getmtime(item_path) > 3600:
                                os.unlink(item_path)
                                print(f"Auto-cleaned: {item_path}")
                        elif os.path.isdir(item_path):
                            # Delete folders older than 1 hour
                            if time.time() - os.path.getmtime(item_path) > 3600:
                                shutil.rmtree(item_path)
                                print(f"Auto-cleaned folder: {item_path}")
                                
        except Exception as e:
            print(f"Scheduled cleanup error: {e}")

# Start cleanup thread
cleanup_thread = threading.Thread(target=scheduled_cleanup, daemon=True)
cleanup_thread.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)