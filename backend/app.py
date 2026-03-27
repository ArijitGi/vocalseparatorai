print("SERVER VERSION 3 - FIXED")

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

# Enhanced CORS configuration
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://your-vercel-frontend.vercel.app", "http://localhost:3000"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Type", "Content-Disposition"]
    }
})

BASE_DIR = os.getcwd()

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
SEPARATED_FOLDER = os.path.join(BASE_DIR, "separated")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SEPARATED_FOLDER, exist_ok=True)

MODEL = "htdemucs_ft"

progress_status = {}
start_times = {}
job_file_mapping = {}  # Store mapping between job_id and original filename

def run_demucs_background(filepath, job_id, original_filename=None):
    try:
        print(f"JOB START: {job_id}")
        print(f"Filepath: {filepath}")
        
        start_times[job_id] = time.time()
        progress_status[job_id] = 5
        
        filepath = os.path.abspath(filepath)
        
        # Get the actual filename without extension for demucs output
        # For uploaded files, filename is job_id, but we need to pass the original name to demucs
        # Actually demucs will use the filename (without extension) of the input file
        # We need to ensure the filename is consistent
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
                    
                    # Update progress based on output
                    if "Separating" in line:
                        progress_status[job_id] = min(progress_status[job_id] + 10, 90)
            
            time.sleep(1)
        
        process.wait()
        
        print(f"Process finished with return code: {process.returncode}")
        
        # Find the output folder - demucs creates folder based on input filename
        result_folder = os.path.join(SEPARATED_FOLDER, MODEL, filename_without_ext)
        
        # If not found, try to find any folder containing the filename
        if not os.path.exists(result_folder):
            possible_folders = os.listdir(os.path.join(SEPARATED_FOLDER, MODEL))
            for folder in possible_folders:
                if filename_without_ext in folder or folder.startswith(filename_without_ext):
                    result_folder = os.path.join(SEPARATED_FOLDER, MODEL, folder)
                    break
        
        vocals = os.path.join(result_folder, "vocals.wav")
        
        print(f"Looking for vocals at: {vocals}")
        
        wait_count = 0
        while not os.path.exists(vocals) and wait_count < 600:
            time.sleep(1)
            wait_count += 1
            
            # Check if file exists in the expected location
            if wait_count % 10 == 0:
                print(f"Waiting for vocals... {wait_count} seconds")
        
        if os.path.exists(vocals):
            print(f"Found vocals at: {vocals}")
            progress_status[job_id] = 100
            print(f"JOB DONE: {job_id}")
        else:
            print(f"TIMEOUT: vocals not found at {vocals}")
            progress_status[job_id] = 0
            
            # List contents of separated folder for debugging
            model_path = os.path.join(SEPARATED_FOLDER, MODEL)
            if os.path.exists(model_path):
                print(f"Contents of {model_path}: {os.listdir(model_path)}")
                for folder in os.listdir(model_path):
                    folder_path = os.path.join(model_path, folder)
                    if os.path.isdir(folder_path):
                        print(f"Contents of {folder}: {os.listdir(folder_path)}")
        
    except Exception as e:
        print(f"ERROR in demucs: {e}")
        import traceback
        traceback.print_exc()
        progress_status[job_id] = 0

@app.route("/api/upload", methods=["POST"])
def upload():
    try:
        file = request.files.get("file")
        
        if not file:
            return jsonify({"error": "No file provided"}), 400
        
        job_id = str(uuid.uuid4())
        
        # Get original filename without extension
        original_name = os.path.splitext(file.filename)[0]
        # Sanitize filename (remove spaces, special chars)
        original_name = "".join(c for c in original_name if c.isalnum() or c in (' ', '-', '_')).replace(' ', '_')
        
        # Save with job_id as filename for uniqueness
        filename = f"{job_id}.mp3"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Rename the file to original name for demucs to output with correct name
        # But we need to maintain the mapping
        original_filepath = os.path.join(UPLOAD_FOLDER, f"{original_name}_{job_id}.mp3")
        os.rename(filepath, original_filepath)
        
        # Store mapping for result retrieval
        job_file_mapping[job_id] = original_name
        
        print(f"Job {job_id}: Original filename {original_name}, saved as {original_filepath}")
        
        # Start background processing
        thread = threading.Thread(
            target=run_demucs_background,
            args=(original_filepath, job_id),
            daemon=True
        )
        thread.start()
        
        return jsonify({"job_id": job_id})
        
    except Exception as e:
        print(f"Upload error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/youtube", methods=["POST"])
def youtube():
    try:
        url = request.json.get("url")
        
        if not url:
            return jsonify({"error": "No URL provided"}), 400
        
        job_id = str(uuid.uuid4())
        progress_status[job_id] = 10
        start_times[job_id] = time.time()
        
        # Create output filename with job_id
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
            "extractaudio": True
        }
        
        print(f"Downloading YouTube video: {url}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', job_id)
            # Sanitize title for filename
            title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).replace(' ', '_')
        
        progress_status[job_id] = 15
        
        # Find the downloaded file
        filepath = os.path.join(UPLOAD_FOLDER, f"{job_id}.mp3")
        
        if not os.path.exists(filepath):
            # Try to find any mp3 file with job_id in name
            files = os.listdir(UPLOAD_FOLDER)
            for f in files:
                if job_id in f and f.endswith('.mp3'):
                    filepath = os.path.join(UPLOAD_FOLDER, f)
                    break
        
        if not os.path.exists(filepath):
            return jsonify({"error": "Download failed - file not found"}), 500
        
        # Store mapping
        job_file_mapping[job_id] = title
        
        print(f"YouTube job {job_id}: Title {title}, file {filepath}")
        
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
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/api/progress/<job_id>", methods=["GET"])
def progress(job_id):
    progress = progress_status.get(job_id, 0)
    
    if job_id in start_times:
        elapsed = int(time.time() - start_times[job_id])
    else:
        elapsed = 0
    
    return jsonify({
        "progress": progress,
        "elapsed": elapsed,
        "estimate": 300
    })

@app.route("/api/result/<job_id>", methods=["GET"])
def result(job_id):
    try:
        # Get the original filename from mapping
        original_name = job_file_mapping.get(job_id)
        
        if not original_name:
            # Try to find by scanning folders
            model_path = os.path.join(SEPARATED_FOLDER, MODEL)
            if os.path.exists(model_path):
                for folder in os.listdir(model_path):
                    if job_id in folder:
                        original_name = folder
                        break
        
        if original_name:
            # Try to find folder with this name
            result_folder = os.path.join(SEPARATED_FOLDER, MODEL, original_name)
            
            # Try alternative folder names
            if not os.path.exists(result_folder):
                # Try with job_id in name
                alt_folder = os.path.join(SEPARATED_FOLDER, MODEL, f"{original_name}_{job_id}")
                if os.path.exists(alt_folder):
                    result_folder = alt_folder
        
        # If still not found, try to find any folder containing job_id
        if not os.path.exists(result_folder):
            model_path = os.path.join(SEPARATED_FOLDER, MODEL)
            if os.path.exists(model_path):
                for folder in os.listdir(model_path):
                    if job_id in folder:
                        result_folder = os.path.join(SEPARATED_FOLDER, MODEL, folder)
                        break
        
        # Check if folder exists
        if not os.path.exists(result_folder):
            print(f"Result folder not found for job {job_id}")
            return jsonify({"status": "processing"})
        
        vocals = os.path.join(result_folder, "vocals.wav")
        instrumental = os.path.join(result_folder, "no_vocals.wav")
        
        if not os.path.exists(vocals):
            print(f"Vocals not found at {vocals}")
            return jsonify({"status": "processing"})
        
        # Get base URL from request
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
        # Find the result folder
        result_folder = None
        
        # Try to find by original name
        original_name = job_file_mapping.get(job_id)
        if original_name:
            folder_path = os.path.join(SEPARATED_FOLDER, MODEL, original_name)
            if os.path.exists(folder_path):
                result_folder = folder_path
        
        # If not found, search by job_id
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
        
        if not file_path:
            return "File not specified", 400
        
        if not os.path.exists(file_path):
            return "File not found", 404
        
        return send_file(
            file_path,
            mimetype="audio/wav",
            as_attachment=False,
            download_name=os.path.basename(file_path)
        )
        
    except Exception as e:
        print(f"Download error: {e}")
        return str(e), 500

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )