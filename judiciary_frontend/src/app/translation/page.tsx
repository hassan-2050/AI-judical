"use client";

import { useState, useEffect } from "react";
import { translationAPI } from "@/lib/api";
import type { TranslationResult, GlossaryTerm } from "@/types";
import { FiGlobe, FiArrowRight, FiBookOpen, FiRefreshCw } from "react-icons/fi";
import toast from "react-hot-toast";

export default function TranslationPage() {
  const [input, setInput] = useState("");
  const [result, setResult] = useState<TranslationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [glossary, setGlossary] = useState<GlossaryTerm[]>([]);
  const [showGlossary, setShowGlossary] = useState(false);
  const [glossarySearch, setGlossarySearch] = useState("");
  const [sourceLang, setSourceLang] = useState("auto");
  const [targetLang, setTargetLang] = useState("auto");

  useEffect(() => {
    loadGlossary();
  }, []);

  async function loadGlossary() {
    try {
      const res = await translationAPI.glossary();
      setGlossary(res.data.glossary || []);
    } catch {}
  }

  async function handleTranslate() {
    if (!input.trim()) return;
    setLoading(true);
    try {
      const res = await translationAPI.translate({
        text: input.trim(),
        source_lang: sourceLang,
        target_lang: targetLang,
      });
      setResult(res.data);
    } catch {
      toast.error("Translation failed");
    } finally {
      setLoading(false);
    }
  }

  function swapLanguages() {
    const newSource = targetLang === "auto" ? "en" : targetLang;
    const newTarget = sourceLang === "auto" ? "ur" : sourceLang;
    setSourceLang(newSource);
    setTargetLang(newTarget);
    if (result) {
      setInput(result.translated_text);
      setResult(null);
    }
  }

  const filteredGlossary = glossary.filter(
    (g) =>
      g.english.toLowerCase().includes(glossarySearch.toLowerCase()) ||
      g.urdu.includes(glossarySearch)
  );

  return (
    <div className="page-container">
      <h1 className="page-title">
        <FiGlobe className="inline mr-2 text-primary-600" />
        Legal Translation
      </h1>
      <p className="text-gray-500 -mt-4 mb-8">
        Translate legal text between English and Urdu with legal terminology support
      </p>

      {/* Translation Area */}
      <div className="grid lg:grid-cols-2 gap-4 mb-8">
        {/* Source */}
        <div className="card">
          <div className="flex items-center justify-between mb-3">
            <select
              value={sourceLang}
              onChange={(e) => setSourceLang(e.target.value)}
              className="text-sm border rounded-lg px-3 py-1.5 font-medium"
            >
              <option value="auto">Auto Detect</option>
              <option value="en">English</option>
              <option value="ur">اردو (Urdu)</option>
            </select>
            <button
              onClick={swapLanguages}
              className="p-2 hover:bg-gray-100 rounded-full transition"
              title="Swap languages"
            >
              <FiRefreshCw size={16} />
            </button>
          </div>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Enter legal text to translate..."
            rows={8}
            className="input resize-none"
            dir={sourceLang === "ur" ? "rtl" : "ltr"}
          />
          <div className="flex justify-between items-center mt-3">
            <span className="text-xs text-gray-400">
              {input.length} characters
            </span>
            <button
              onClick={handleTranslate}
              disabled={!input.trim() || loading}
              className="btn-primary flex items-center gap-2"
            >
              {loading ? "Translating..." : "Translate"}
              <FiArrowRight size={16} />
            </button>
          </div>
        </div>

        {/* Target */}
        <div className="card">
          <div className="flex items-center justify-between mb-3">
            <select
              value={targetLang}
              onChange={(e) => setTargetLang(e.target.value)}
              className="text-sm border rounded-lg px-3 py-1.5 font-medium"
            >
              <option value="auto">Auto (opposite)</option>
              <option value="en">English</option>
              <option value="ur">اردو (Urdu)</option>
            </select>
          </div>
          <div
            className="min-h-[200px] bg-gray-50 rounded-lg p-3 text-sm"
            dir={result?.target_lang === "ur" ? "rtl" : "ltr"}
          >
            {result ? (
              <p className="whitespace-pre-wrap">{result.translated_text}</p>
            ) : (
              <p className="text-gray-400 italic">Translation will appear here...</p>
            )}
          </div>
          {result && (
            <div className="mt-3">
              <p className="text-xs text-gray-400">
                {result.source_lang === "en" ? "English" : "Urdu"} →{" "}
                {result.target_lang === "en" ? "English" : "Urdu"} •{" "}
                {result.terms_translated.length} legal terms translated
              </p>
              {result.is_partial && (
                <p className="text-xs text-amber-600 mt-1">
                  ⚠ {result.note}
                </p>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Terms translated */}
      {result && result.terms_translated.length > 0 && (
        <div className="card mb-8">
          <h2 className="font-semibold text-lg mb-3">Legal Terms Found</h2>
          <div className="flex flex-wrap gap-2">
            {result.terms_translated.map((t, i) => (
              <div
                key={i}
                className="bg-primary-50 border border-primary-200 rounded-lg px-3 py-1.5 text-sm"
              >
                <span className="font-medium text-primary-700">{t.original}</span>
                <span className="text-gray-400 mx-2">→</span>
                <span className="text-gray-700">{t.translated}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Glossary Toggle */}
      <div className="card">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-lg flex items-center gap-2">
            <FiBookOpen className="text-primary-600" />
            Legal Glossary ({glossary.length} terms)
          </h2>
          <button
            onClick={() => setShowGlossary(!showGlossary)}
            className="btn-secondary text-sm"
          >
            {showGlossary ? "Hide" : "Show"} Glossary
          </button>
        </div>

        {showGlossary && (
          <div className="mt-4">
            <input
              type="text"
              placeholder="Search glossary..."
              value={glossarySearch}
              onChange={(e) => setGlossarySearch(e.target.value)}
              className="input mb-4"
            />
            <div className="max-h-96 overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-white">
                  <tr className="border-b text-left text-gray-500">
                    <th className="pb-2 font-medium">English</th>
                    <th className="pb-2 font-medium text-right" dir="rtl">اردو</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {filteredGlossary.map((g, i) => (
                    <tr key={i} className="hover:bg-gray-50">
                      <td className="py-2">{g.english}</td>
                      <td className="py-2 text-right" dir="rtl">{g.urdu}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
