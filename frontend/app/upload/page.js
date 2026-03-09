"use client";

import { useState, useEffect } from "react";
import { UploadCloud, FileMusic, Wand2, Download } from "lucide-react";
import { uploadFile, getProgress, getResult } from "../../services/api";
import { useJobStore } from "@/store/jobStore";

export default function UploadPage() {
  const [file, setFile] = useState(null);

  const { uploadJob, startJob, setProgress, finishJob } =
    useJobStore();

  // Poll ONLY upload job
  useEffect(() => {
    if (!uploadJob?.id) return;

    const interval = setInterval(async () => {
      const p = await getProgress(uploadJob.id);
      setProgress("upload", p);

      if (p === 100) {
        const res = await getResult(uploadJob.id);
        if (res.status === "done") {
          finishJob("upload", res);
          clearInterval(interval);
        }
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [uploadJob?.id, setProgress, finishJob]);

  const handleUpload = async () => {
    if (!file) return;
    const id = await uploadFile(file);
    startJob(id, "upload");
  };

  return (
    <div className="max-w-3xl mx-auto py-16">
      {/* TITLE */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900">
          Process Your Track
        </h1>
        <p className="mt-3 text-gray-500">
          Upload your song and let our AI separate the magic.
        </p>
      </div>

      {/* UPLOAD CARD */}
      {!file && !uploadJob?.isProcessing && !uploadJob?.result && (
        <div className="bg-white rounded-3xl shadow-sm border p-10 text-center">
          <div className="flex justify-center mb-6">
            <div className="w-20 h-20 bg-red-50 rounded-full flex items-center justify-center">
              <UploadCloud size={36} className="text-red-500" />
            </div>
          </div>

          <h3 className="text-xl font-semibold text-gray-900">
            Upload Your Song
          </h3>
          <p className="text-gray-500 mt-2">
            Supports MP3, WAV, FLAC, M4A up to 50MB
          </p>

          <label className="mt-6 inline-block bg-red-500 text-white px-6 py-3 rounded-xl cursor-pointer hover:bg-red-600 transition">
            Select File
            <input
              type="file"
              hidden
              onChange={(e) => setFile(e.target.files[0])}
            />
          </label>
        </div>
      )}

      {/* FILE PREVIEW */}
      {file && !uploadJob?.isProcessing && !uploadJob?.result && (
        <div className="mt-8 bg-white rounded-2xl border p-6">
          <div className="flex items-center gap-4">
            <FileMusic className="text-gray-500" />
            <div className="flex-1">
              <p className="font-medium text-gray-900 truncate">
                {file.name}
              </p>
              <p className="text-sm text-gray-400">
                {(file.size / 1024 / 1024).toFixed(1)} MB • Ready to process
              </p>
            </div>
          </div>

          <button
            onClick={handleUpload}
            className="mt-6 w-full bg-black text-white py-3 rounded-xl hover:opacity-90 transition flex items-center justify-center gap-2 cursor-pointer"
          >
            <Wand2 size={18} />
            Start Separation
          </button>
        </div>
      )}

      {/* PROGRESS */}
      {uploadJob?.isProcessing && (
        <div className="mt-10 bg-white rounded-3xl shadow-sm border p-10 text-center">
          <div className="relative w-40 h-40 mx-auto">
            <div className="absolute inset-0 flex items-center justify-center text-2xl font-bold">
              {uploadJob.progress}%
            </div>

            <svg className="w-40 h-40 transform -rotate-90">
              <circle
                cx="80"
                cy="80"
                r="70"
                stroke="#eee"
                strokeWidth="12"
                fill="none"
              />
              <circle
                cx="80"
                cy="80"
                r="70"
                stroke="#ef4444"
                strokeWidth="12"
                fill="none"
                strokeDasharray={440}
                strokeDashoffset={
                  440 - (440 * uploadJob.progress) / 100
                }
                strokeLinecap="round"
              />
            </svg>
          </div>

          <h3 className="mt-6 text-lg font-semibold text-gray-900">
            Removing vocals...
          </h3>
          <p className="text-gray-500">
            Please wait, AI is working its magic
          </p>
        </div>
      )}

      {/* RESULTS */}
      {uploadJob?.result && (
        <div className="mt-12 space-y-6">
          <div className="flex justify-between items-center">
            <h3 className="text-xl font-semibold text-gray-900">
              Processing Complete
            </h3>
            <span className="bg-green-100 text-green-600 text-sm px-3 py-1 rounded-full">
              Success
            </span>
          </div>

          <div className="bg-white border rounded-2xl p-6">
            <h4 className="font-semibold mb-4">Vocals</h4>
            <a
              href={uploadJob.result.vocals}
              className="bg-red-500 text-white px-6 py-3 rounded-xl inline-flex items-center gap-2 hover:bg-red-600 transition cursor-pointer"
            >
              <Download size={18} />
              Download Vocals
            </a>
          </div>

          <div className="bg-white border rounded-2xl p-6">
            <h4 className="font-semibold mb-4">Instrumental</h4>
            <a
              href={uploadJob.result.instrumental}
              className="bg-black text-white px-6 py-3 rounded-xl inline-flex items-center gap-2 hover:opacity-90 transition cursor-pointer"
            >
              <Download size={18} />
              Download Drums
            </a>
            <a
              href={uploadJob.result.bass}
              className="bg-black text-white px-6 py-3 rounded-xl inline-flex items-center gap-2 hover:opacity-90 transition cursor-pointer"
            >
              <Download size={18} />
              Download Bass
            </a>
            <a
              href={uploadJob.result.other}
              className="bg-black text-white px-6 py-3 rounded-xl inline-flex items-center gap-2 hover:opacity-90 transition cursor-pointer"
            >
              <Download size={18} />
              Download Other Instruments
            </a>
          </div>
        </div>
      )}

      <div className="mt-20 text-center text-gray-400 text-sm">
        © 2023 VocalRemover. Made with love for music.
      </div>
    </div>
  );
}