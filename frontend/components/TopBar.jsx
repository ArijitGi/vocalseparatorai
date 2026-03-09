"use client";

export default function Topbar({ setOpen }) {
  return (
    <div className="flex items-center justify-between bg-white shadow px-6 py-4">
      <button
        onClick={() => setOpen(true)}
        className="md:hidden text-2xl cursor-pointer"
      >
        ☰
      </button>

      <h2 className="text-xl font-semibold">
        AI Vocal Remover
      </h2>

      <div />
    </div>
  );
}