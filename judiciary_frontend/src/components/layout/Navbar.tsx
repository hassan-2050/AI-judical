"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useEffect } from "react";
import {
  FiMenu,
  FiX,
  FiSearch,
  FiDatabase,
  FiBarChart2,
  FiSettings,
  FiLogIn,
  FiLogOut,
  FiHome,
  FiLayout,
  FiMessageSquare,
  FiFile,
  FiFileText,
  FiBriefcase,
  FiGlobe,
  FiUser,
} from "react-icons/fi";

const navLinks = [
  { href: "/", label: "Home", icon: <FiHome size={18} /> },
  { href: "/dashboard", label: "Dashboard", icon: <FiLayout size={18} /> },
  { href: "/cases", label: "Cases", icon: <FiDatabase size={18} /> },
  { href: "/search", label: "Search", icon: <FiSearch size={18} /> },
  { href: "/ai-assistant", label: "Munsif AI", icon: <FiMessageSquare size={18} /> },
  { href: "/documents", label: "Documents", icon: <FiFile size={18} /> },
  { href: "/templates", label: "Templates", icon: <FiFileText size={18} /> },
  { href: "/lawyers", label: "Lawyers", icon: <FiBriefcase size={18} /> },
  { href: "/translation", label: "Translate", icon: <FiGlobe size={18} /> },
  { href: "/analytics", label: "Analytics", icon: <FiBarChart2 size={18} /> },
];

export default function Navbar() {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);
  const [user, setUser] = useState<{ first_name: string } | null>(null);

  useEffect(() => {
    const stored = localStorage.getItem("user");
    if (stored) {
      try {
        setUser(JSON.parse(stored));
      } catch {}
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setUser(null);
    window.location.href = "/";
  };

  return (
    <nav className="sticky top-0 z-50 bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 font-display font-bold text-xl text-judiciary-dark">
          <span className="text-judiciary-gold">⚖</span> Munsif AI
        </Link>

        {/* Desktop nav */}
        <div className="hidden md:flex items-center gap-1">
          {navLinks.map((l) => {
            const active = pathname === l.href;
            return (
              <Link
                key={l.href}
                href={l.href}
                className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition ${
                  active
                    ? "bg-primary-50 text-primary-700"
                    : "text-gray-600 hover:bg-gray-100"
                }`}
              >
                {l.icon}
                {l.label}
              </Link>
            );
          })}
        </div>

        {/* Auth */}
        <div className="hidden md:flex items-center gap-3">
          {user ? (
            <>
              <Link
                href="/profile"
                className="text-sm text-gray-600 hover:text-primary-600 flex items-center gap-1"
              >
                <FiUser size={14} /> {user.first_name}
              </Link>
              <button onClick={handleLogout} className="btn-secondary text-sm flex items-center gap-1">
                <FiLogOut size={16} /> Logout
              </button>
            </>
          ) : (
            <Link href="/login" className="btn-primary text-sm flex items-center gap-1">
              <FiLogIn size={16} /> Login
            </Link>
          )}
        </div>

        {/* Mobile hamburger */}
        <button
          className="md:hidden p-2"
          onClick={() => setMenuOpen(!menuOpen)}
        >
          {menuOpen ? <FiX size={24} /> : <FiMenu size={24} />}
        </button>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className="md:hidden border-t bg-white px-4 pb-4">
          {navLinks.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              onClick={() => setMenuOpen(false)}
              className={`flex items-center gap-2 px-3 py-3 rounded-lg text-sm ${
                pathname === l.href
                  ? "bg-primary-50 text-primary-700 font-medium"
                  : "text-gray-600"
              }`}
            >
              {l.icon}
              {l.label}
            </Link>
          ))}
          <div className="mt-2 pt-2 border-t">
            {user ? (
              <button onClick={handleLogout} className="w-full btn-secondary text-sm">
                Logout
              </button>
            ) : (
              <Link href="/login" onClick={() => setMenuOpen(false)} className="block text-center btn-primary text-sm">
                Login
              </Link>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}
