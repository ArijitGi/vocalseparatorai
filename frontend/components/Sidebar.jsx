"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, Music2, Upload, Youtube } from "lucide-react";

export default function Sidebar({ open, setOpen }) {
  const pathname = usePathname();

  const navItems = [
    { href: "/", label: "Home", icon: Music2 },
    { href: "/upload", label: "Upload Song", icon: Upload },
    { href: "/converter", label: "YouTube Song", icon: Youtube },
  ];

  return (
    <aside
      className={`
        fixed left-0 top-0 h-screen bg-white border-r border-gray-200
        transition-all duration-300 ease-in-out
        ${open ? "w-64" : "w-20"}
        flex flex-col justify-between
        shadow-sm
      `}
    >
      {/* TOP SECTION */}
      <div>
        {/* Toggle Button */}
        <div className="flex items-center justify-between p-5">
          {open && (
            <div className="flex items-center gap-2">
              {/* <Music2 className="text-red-500" /> */}
              <span className="font-semibold text-gray-900">
                VocalSeperator
              </span>
            </div>
          )}

          <button
            onClick={() => setOpen(!open)}
            className="p-2 rounded-lg hover:bg-gray-100 transition cursor-pointer"
          >
            <Menu size={20} />
          </button>
        </div>

        {/* NAVIGATION */}
        <div className="mt-6 space-y-2 px-3">
          {navItems.map(({ href, label, icon: Icon }) => {
            const active = pathname === href;

            return (
              <Link
                key={href}
                href={href}
                className={`
                  flex items-center
                  ${open ? "justify-start px-4" : "justify-center"}
                  py-3 rounded-xl
                  transition-all duration-200
                  ${
                    active
                      ? "bg-red-100 text-red-500"
                      : "text-gray-600 hover:bg-gray-100"
                  }
                `}
              >
                <Icon size={20} />
                {open && (
                  <span className="ml-3 font-medium">{label}</span>
                )}
              </Link>
            );
          })}
        </div>
      </div>

      {/* BOTTOM PRICING */}
      {open && (
        <div className="p-5">
          <div className="bg-red-50 border border-red-100 rounded-2xl p-5">
            <h4 className="font-semibold text-gray-900">Pro Plan</h4>
            <p className="text-sm text-gray-500 mt-1">
              Unlimited conversions & faster speed.
            </p>
            <button className="mt-4 w-full bg-red-500 text-white py-2 rounded-xl hover:bg-red-600 transition cursor-pointer">
              Upgrade Now
            </button>
          </div>
        </div>
      )}
    </aside>
  );
}