"use client";

import { useEffect, useState } from "react";
import { getProgress, getResult } from "../services/api";

export default function ProgressBar({ jobId }) {
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);

  useEffect(() => {
    if (!jobId) return;

    const interval = setInterval(async () => {
      const percent = await getProgress(jobId);
      setProgress(percent);

      if (percent === 100) {
        clearInterval(interval);
        const res = await getResult(jobId);
        setResult(res);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [jobId]);

  return (
    <div className="mt-6 bg-white p-6 rounded-xl shadow-md">
      <div className="text-lg font-semibold mb-2">
        Removing vocals... {progress}%
      </div>

      <div className="w-full bg-gray-200 rounded-full h-4">
        <div
          className="bg-red-500 h-4 rounded-full transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>

      {result?.status === "done" && (
        <div className="mt-4 text-green-600 font-semibold">
          Processing Complete ✅
        </div>
      )}
    </div>
  );
}