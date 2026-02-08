"use client";

import Link from "next/link";
import {
  FiSearch,
  FiDatabase,
  FiBarChart2,
  FiDownloadCloud,
  FiMessageSquare,
  FiFile,
  FiFileText,
  FiBriefcase,
  FiGlobe,
  FiCpu,
} from "react-icons/fi";

const features = [
  {
    icon: <FiMessageSquare className="w-8 h-8" />,
    title: "Munsif AI Assistant",
    desc: "AI-powered legal assistant for case research, predictions, and bilingual legal guidance in English and Urdu.",
    href: "/ai-assistant",
  },
  {
    icon: <FiSearch className="w-8 h-8" />,
    title: "Advanced Search",
    desc: "Search across thousands of court cases by keywords, judges, courts, statutes, and more.",
    href: "/search",
  },
  {
    icon: <FiDatabase className="w-8 h-8" />,
    title: "Case Database",
    desc: "Browse the complete database of Pakistan legal cases from Supreme Court and High Courts.",
    href: "/cases",
  },
  {
    icon: <FiCpu className="w-8 h-8" />,
    title: "NER & Summarization",
    desc: "Automatic entity extraction, case summaries, and similar case finding powered by AI.",
    href: "/documents",
  },
  {
    icon: <FiFile className="w-8 h-8" />,
    title: "Document Management",
    desc: "Upload, process, and analyze legal documents with AI-powered text extraction and entity recognition.",
    href: "/documents",
  },
  {
    icon: <FiFileText className="w-8 h-8" />,
    title: "Legal Templates",
    desc: "Generate professional legal documents from templates including petitions, affidavits, and notices.",
    href: "/templates",
  },
  {
    icon: <FiBriefcase className="w-8 h-8" />,
    title: "Lawyer Directory",
    desc: "Find verified legal professionals across Pakistan, filtered by city, specialization, and ratings.",
    href: "/lawyers",
  },
  {
    icon: <FiGlobe className="w-8 h-8" />,
    title: "Legal Translation",
    desc: "Translate legal text between English and Urdu with specialized legal terminology support.",
    href: "/translation",
  },
  {
    icon: <FiBarChart2 className="w-8 h-8" />,
    title: "Analytics Dashboard",
    desc: "Visualize case trends, court statistics, judge activity, and more with interactive charts.",
    href: "/analytics",
  },
  {
    icon: <FiDownloadCloud className="w-8 h-8" />,
    title: "Live Scraping",
    desc: "Scrape real-time case data from Pakistani court websites and keep the database up to date.",
    href: "/scraper",
  },
];

export default function HomePage() {
  return (
    <div className="flex flex-col">
      {/* Hero */}
      <section className="bg-gradient-to-br from-judiciary-dark via-judiciary-navy to-judiciary-blue text-white">
        <div className="max-w-7xl mx-auto px-4 py-24 sm:py-32 text-center">
          <h1 className="text-4xl sm:text-6xl font-display font-bold tracking-tight mb-6">
            Munsif
            <span className="text-judiciary-gold"> AI</span>
          </h1>
          <p className="text-lg sm:text-xl text-gray-300 max-w-3xl mx-auto mb-10">
            A comprehensive platform to search, browse, and analyze court cases
            from Pakistan&apos;s Supreme Court, High Courts, and more — powered
            by real-time web scraping.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/search"
              className="px-8 py-3 bg-judiciary-gold text-judiciary-dark font-semibold rounded-lg hover:bg-yellow-400 transition"
            >
              Search Cases
            </Link>
            <Link
              href="/dashboard"
              className="px-8 py-3 border border-white/30 rounded-lg hover:bg-white/10 transition"
            >
              View Dashboard
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="max-w-7xl mx-auto px-4 py-20">
        <h2 className="text-3xl font-display font-bold text-center mb-12">
          Platform Features
        </h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6">
          {features.map((f) => (
            <Link
              key={f.title}
              href={f.href}
              className="group p-6 bg-white rounded-xl shadow-sm border border-gray-100 hover:shadow-lg hover:border-primary-200 transition"
            >
              <div className="text-primary-600 mb-4">{f.icon}</div>
              <h3 className="text-lg font-semibold mb-2 group-hover:text-primary-600 transition">
                {f.title}
              </h3>
              <p className="text-gray-600 text-sm">{f.desc}</p>
            </Link>
          ))}
        </div>
      </section>

      {/* Stats preview */}
      <section className="bg-white border-t">
        <div className="max-w-7xl mx-auto px-4 py-16">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            {[
              { label: "Court Cases", value: "10,000+" },
              { label: "Courts Covered", value: "7+" },
              { label: "Active Scrapers", value: "3" },
              { label: "Updated Daily", value: "✓" },
            ].map((s) => (
              <div key={s.label}>
                <div className="text-3xl font-bold text-primary-600 mb-1">
                  {s.value}
                </div>
                <div className="text-gray-500 text-sm">{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-judiciary-dark text-gray-400 py-8">
        <div className="max-w-7xl mx-auto px-4 text-center text-sm">
          <p>© {new Date().getFullYear()} Munsif AI. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
