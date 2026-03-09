"use client";

import { useState } from "react";
import Sidebar from "./Sidebar";

export default function DashboardLayout({ children }) {
  const [open, setOpen] = useState(true);

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar open={open} setOpen={setOpen} />
      <main
        className={`transition-all duration-300 ease-in-out
    ${open ? "ml-64" : "ml-20"}
    flex-1 p-16`}
      >
        {children}
      </main>
    </div>
  );
}