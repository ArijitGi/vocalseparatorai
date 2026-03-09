"use client";

export default function DownloadLinks({ vocals, instrumental }) {
  return (
    <div className="mt-6 flex gap-4">
      <a
        href={`http://localhost:5000/download?file=${vocals}`}
        className="px-4 py-2 bg-green-600 text-white rounded-lg"
      >
        Download Vocals
      </a>

      <a
        href={`http://localhost:5000/download?file=${instrumental}`}
        className="px-4 py-2 bg-blue-600 text-white rounded-lg"
      >
        Download Instrumental
      </a>
    </div>
  );
}