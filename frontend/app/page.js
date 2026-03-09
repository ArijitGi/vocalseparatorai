"use client";
import Image from "next/image";

export default function Home() {
  return (
    <div className="grid grid-cols-2 gap-16 items-center">
      
      {/* LEFT CONTENT */}
      <div>
        <h1 className="text-6xl font-extrabold text-gray-900 leading-[1.1]">
          Use your own voice and spread the magic into the world
        </h1>

        <p className="mt-6 text-lg text-gray-500 max-w-xl">
          Professional quality vocal isolation for music lovers.
          Remove vocals from any song in seconds.
        </p>

        <button className="mt-8 bg-red-500 hover:bg-red-600 transition text-white px-8 py-4 rounded-2xl text-lg font-semibold shadow-lg cursor-pointer">
          Start Removing Vocals
        </button>
      </div>

      {/* RIGHT IMAGE */}
      <div className="relative w-full h-[520px]">
  <Image
    src="https://images.unsplash.com/photo-1511379938547-c1f69419868d"
    alt="Microphone"
    fill
    className="rounded-3xl shadow-xl object-cover"
    priority
  />
</div>

    </div>
  );
}