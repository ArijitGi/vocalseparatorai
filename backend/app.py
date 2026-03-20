import os
import uuid
import subprocess
import yt_dlp
import threading
import time
import sys
import zipfile
from io import BytesIO

from flask import Flask,request,jsonify,send_file
from flask_cors import CORS

app=Flask(__name__)

CORS(app)

BASE_DIR=os.getcwd()

UPLOAD_FOLDER=os.path.join(BASE_DIR,"uploads")
SEPARATED_FOLDER=os.path.join(BASE_DIR,"separated")

os.makedirs(UPLOAD_FOLDER,exist_ok=True)
os.makedirs(SEPARATED_FOLDER,exist_ok=True)

MODEL="htdemucs_ft"

progress_status={}
start_times={}


def run_demucs_background(filepath,job_id):

    try:

        print("JOB START:",job_id)

        start_times[job_id]=time.time()

        progress_status[job_id]=5

        filepath=os.path.abspath(filepath)

        filename=os.path.splitext(
            os.path.basename(filepath)
        )[0]

        process=subprocess.Popen(

            [
                sys.executable,
                "-m",
                "demucs",

                "-n",MODEL,

                "--two-stems","vocals",

                filepath
            ],

            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        while process.poll() is None:

            if process.stdout:

                line=process.stdout.readline()

                if line:
                    print(line.strip())

            if progress_status.get(job_id,5) < 90:
                progress_status[job_id]+=1

            time.sleep(2)

        process.wait()

        print("PROCESS FINISHED")

        result_folder=os.path.join(
            SEPARATED_FOLDER,
            MODEL,
            filename
        )

        vocals=os.path.join(result_folder,"vocals.wav")

        wait_count=0

        while not os.path.exists(vocals):

            time.sleep(1)

            wait_count+=1

            if wait_count>600:

                print("TIMEOUT")

                progress_status[job_id]=0

                return

        progress_status[job_id]=100

        print("JOB DONE")

    except Exception as e:

        print("ERROR:",e)

        progress_status[job_id]=0



@app.route("/api/upload",methods=["POST"])
def upload():

    file=request.files.get("file")

    if not file:

        return jsonify({"error":"No file"})

    job_id=str(uuid.uuid4())

    filepath=os.path.join(
        UPLOAD_FOLDER,
        job_id+".mp3"
    )

    file.save(filepath)

    threading.Thread(

        target=run_demucs_background,
        args=(filepath,job_id),
        daemon=True

    ).start()

    return jsonify({"job_id":job_id})



@app.route("/api/youtube",methods=["POST"])
def youtube():

    try:

        url=request.json.get("url")

        if not url:
            return jsonify({"error":"No url"}),400

        job_id=str(uuid.uuid4())

        progress_status[job_id]=10

        start_times[job_id]=time.time()

        output=os.path.join(
            UPLOAD_FOLDER,
            job_id
        )

        ydl_opts={

            "format":"bestaudio",

            "outtmpl":output,

            "postprocessors":[{

                "key":"FFmpegExtractAudio",

                "preferredcodec":"mp3",

                "preferredquality":"320"

            }],

            "quiet":False,

            "noplaylist":True
        }

        yt_dlp.YoutubeDL(ydl_opts).download([url])

        progress_status[job_id]=15

        filepath=output+".mp3"

        if not os.path.exists(filepath):

            return jsonify({
                "error":"Download failed"
            }),500

        threading.Thread(

            target=run_demucs_background,

            args=(filepath,job_id),

            daemon=True

        ).start()

        return jsonify({"job_id":job_id})

    except Exception as e:

        print("YOUTUBE ERROR:",e)

        return jsonify({
            "error":str(e)
        }),500



@app.route("/api/progress/<job_id>")
def progress(job_id):

    progress=progress_status.get(job_id,0)

    if job_id in start_times:

        elapsed=int(
            time.time()-start_times[job_id]
        )

    else:

        elapsed=0

    return jsonify({

        "progress":progress,

        "elapsed":elapsed,

        "estimate":300

    })



@app.route("/api/result/<job_id>")
def result(job_id):

    folder=os.path.join(

        SEPARATED_FOLDER,
        MODEL,
        job_id

    )

    if not os.path.exists(folder):

        possible=os.listdir(

            os.path.join(SEPARATED_FOLDER,MODEL)

        )

        for p in possible:

            if job_id in p:

                folder=os.path.join(

                    SEPARATED_FOLDER,
                    MODEL,
                    p

                )

                break

    vocals=os.path.join(folder,"vocals.wav")

    instrumental=os.path.join(folder,"no_vocals.wav")

    if not os.path.exists(vocals):

        return jsonify({

            "status":"processing"

        })

    base=request.host_url

    return jsonify({

        "status":"done",

        "vocals":base+"api/download?file="+vocals,

        "instrumental":base+"api/download?file="+instrumental,

        "zip":base+"api/download_zip/"+job_id

    })

@app.route("/api/download_zip/<job_id>")
def download_zip(job_id):

    folder=os.path.join(
        SEPARATED_FOLDER,
        MODEL,
        job_id
    )

    if not os.path.exists(folder):

        possible=os.listdir(
            os.path.join(SEPARATED_FOLDER,MODEL)
        )

        for p in possible:

            if job_id in p:

                folder=os.path.join(
                    SEPARATED_FOLDER,
                    MODEL,
                    p
                )

                break

    vocals=os.path.join(folder,"vocals.wav")

    instrumental=os.path.join(folder,"no_vocals.wav")

    if not os.path.exists(vocals):

        return "Not ready",404

    memory_file=BytesIO()

    with zipfile.ZipFile(memory_file,'w') as z:

        z.write(vocals,"vocals.wav")

        z.write(instrumental,"instrumental.wav")

    memory_file.seek(0)

    return send_file(
        memory_file,
        download_name="separated_tracks.zip",
        as_attachment=True
    )

@app.route("/api/download")
def download():

    file=request.args.get("file")

    if not file or not os.path.exists(file):

        return "File not found",404

    return send_file(
        file,
        mimetype="audio/wav",
        as_attachment=False
    )



if __name__=="__main__":

    app.run(
        host="0.0.0.0",
        port=5000
    )