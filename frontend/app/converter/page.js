"use client";

import { useState, useEffect } from "react";
import {
  Link as LinkIcon,
  Wand2,
  Download,
  Mic,
  Piano,
} from "lucide-react";
import { uploadYouTube, getProgress, getResult } from "../../services/api";
import { useJobStore } from "@/store/jobStore";

export default function ConverterPage() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);

  const { youtubeJob, startJob, setProgress, finishJob } =
    useJobStore();

  // Poll ONLY youtube job
  useEffect(() => {
    if (!youtubeJob?.id) return;

    const interval = setInterval(async () => {
      const p = await getProgress(youtubeJob.id);
      setProgress("youtube", p);

      if (p === 100) {
        const res = await getResult(youtubeJob.id);
        if (res.status === "done") {
          finishJob("youtube", res);
          clearInterval(interval);
        }
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [youtubeJob?.id, setProgress, finishJob]);

  const handleConvert = async () => {
    if (!url) return;
    setLoading(true);
    const id = await uploadYouTube(url);
    startJob(id, "youtube");
    setLoading(false);
  };

  return (
    <div className="max-w-3xl mx-auto py-16">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900">
          Convert YouTube to Tracks
        </h1>
        <p className="mt-4 text-gray-500 text-lg">
          Paste a YouTube link below to separate vocals and instrumentals
          instantly using AI.
        </p>
      </div>

      {!youtubeJob?.result && (
        <div className="bg-white rounded-3xl shadow-sm border p-10">
          <div className="relative">
            <LinkIcon className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Paste YouTube URL"
              className="w-full pl-12 pr-4 py-4 rounded-2xl border focus:outline-none focus:ring-2 focus:ring-red-400"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
            />
          </div>

          <button
            onClick={handleConvert}
            disabled={loading}
            className="mt-8 w-full bg-red-500 hover:bg-red-600 transition text-white py-4 rounded-2xl text-lg font-semibold shadow-lg flex items-center justify-center gap-2 cursor-pointer"
          >
            <Wand2 size={20} />
            {loading ? "Processing..." : "Convert and Separate"}
          </button>

          {youtubeJob?.isProcessing && (
            <div className="mt-12">
              <div className="flex justify-between text-sm mb-2">
                <span>Analyzing Audio...</span>
                <span className="text-red-500 font-semibold">
                  {youtubeJob.progress}%
                </span>
              </div>

              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-red-500 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${youtubeJob.progress}%` }}
                ></div>
              </div>
            </div>
          )}
        </div>
      )}

      {youtubeJob?.result && (
  <div className="mt-12 bg-white rounded-3xl shadow-sm border p-10 space-y-6">

    {/* VOCALS */}
    <div className="flex items-center justify-between p-5 border rounded-2xl">
      <div className="flex items-center gap-4">
        <Mic />
        <span>Vocals</span>
      </div>
      <a
        href={youtubeJob.result.vocals}
        className="text-red-500 cursor-pointer"
      >
        <Download />
      </a>
    </div>

    {/* DRUMS */}
    <div className="flex items-center justify-between p-5 border rounded-2xl">
      <div className="flex items-center gap-4">
        <Piano />
        <span>Drums</span>
      </div>
      <a
        href={youtubeJob.result.drums}
        className="text-red-500 cursor-pointer"
      >
        <Download />
      </a>
    </div>

    {/* BASS */}
    <div className="flex items-center justify-between p-5 border rounded-2xl">
      <div className="flex items-center gap-4">
        <Piano />
        <span>Bass</span>
      </div>
      <a
        href={youtubeJob.result.bass}
        className="text-red-500 cursor-pointer"
      >
        <Download />
      </a>
    </div>

    {/* OTHER */}
    <div className="flex items-center justify-between p-5 border rounded-2xl">
      <div className="flex items-center gap-4">
        <Piano />
        <span>Other Instruments</span>
      </div>
      <a
        href={youtubeJob.result.other}
        className="text-red-500 cursor-pointer"
      >
        <Download />
      </a>
    </div>

  </div>
)}

      <div className="mt-20 text-center text-gray-400 text-sm">
        © 2026 VocalSeparatorAI. Made with love for music.
      </div>
    </div>
  );
}