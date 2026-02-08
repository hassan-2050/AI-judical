"use client";

import { useState, useEffect } from "react";
import { templatesAPI } from "@/lib/api";
import type { TemplateCard, LegalTemplate, TemplateCategory } from "@/types";
import { FiFileText, FiDownload, FiCopy, FiChevronRight, FiArrowLeft, FiX } from "react-icons/fi";
import toast from "react-hot-toast";

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<TemplateCard[]>([]);
  const [categories, setCategories] = useState<TemplateCategory[]>([]);
  const [selectedCategory, setSelectedCategory] = useState("");
  const [selectedLang, setSelectedLang] = useState("");
  const [loading, setLoading] = useState(true);
  const [selectedTemplate, setSelectedTemplate] = useState<LegalTemplate | null>(null);
  const [showFillForm, setShowFillForm] = useState(false);
  const [formValues, setFormValues] = useState<Record<string, string>>({});
  const [generatedDoc, setGeneratedDoc] = useState("");

  useEffect(() => {
    loadTemplates();
    loadCategories();
  }, [selectedCategory, selectedLang]);

  async function loadTemplates() {
    setLoading(true);
    try {
      const params: Record<string, unknown> = {};
      if (selectedCategory) params.category = selectedCategory;
      if (selectedLang) params.language = selectedLang;
      const res = await templatesAPI.list(params);
      setTemplates(res.data.templates || []);
    } catch {
      toast.error("Failed to load templates");
    } finally {
      setLoading(false);
    }
  }

  async function loadCategories() {
    try {
      const res = await templatesAPI.categories();
      setCategories(res.data.categories || []);
    } catch {}
  }

  async function viewTemplate(id: string) {
    try {
      const res = await templatesAPI.get(id);
      setSelectedTemplate(res.data.template);
    } catch {
      toast.error("Failed to load template");
    }
  }

  function startFilling() {
    if (!selectedTemplate) return;
    const values: Record<string, string> = {};
    selectedTemplate.placeholders.forEach((p) => {
      values[p] = "";
    });
    setFormValues(values);
    setShowFillForm(true);
    setGeneratedDoc("");
  }

  async function generateDocument() {
    if (!selectedTemplate) return;
    try {
      const res = await templatesAPI.generate(selectedTemplate.id, formValues);
      setGeneratedDoc(res.data.document);
      toast.success("Document generated!");
    } catch {
      toast.error("Generation failed");
    }
  }

  function copyToClipboard(text: string) {
    navigator.clipboard.writeText(text);
    toast.success("Copied to clipboard!");
  }

  function downloadAsText(text: string, filename: string) {
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="page-container">
      <h1 className="page-title">
        <FiFileText className="inline mr-2 text-primary-600" />
        Legal Templates
      </h1>
      <p className="text-gray-500 -mt-4 mb-8">
        Browse and use professional legal document templates for Pakistani courts
      </p>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-6">
        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="input w-auto"
        >
          <option value="">All Categories</option>
          {categories.map((c) => (
            <option key={c.value} value={c.value}>{c.label}</option>
          ))}
        </select>
        <select
          value={selectedLang}
          onChange={(e) => setSelectedLang(e.target.value)}
          className="input w-auto"
        >
          <option value="">All Languages</option>
          <option value="en">English</option>
          <option value="ur">Urdu</option>
          <option value="both">Bilingual</option>
        </select>
      </div>

      {/* Template Selection View */}
      {!selectedTemplate && (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {loading ? (
            <p className="text-gray-400 col-span-full text-center py-12">Loading templates...</p>
          ) : templates.length === 0 ? (
            <p className="text-gray-400 col-span-full text-center py-12">No templates found</p>
          ) : (
            templates.map((t) => (
              <button
                key={t.id}
                onClick={() => viewTemplate(t.id)}
                className="card text-left hover:shadow-md hover:border-primary-200 transition group"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="badge bg-primary-50 text-primary-700 capitalize">
                    {t.category.replace(/_/g, " ")}
                  </span>
                  <FiChevronRight className="text-gray-300 group-hover:text-primary-500 transition" />
                </div>
                <h3 className="font-semibold mb-1">{t.name}</h3>
                {t.description && (
                  <p className="text-sm text-gray-500 line-clamp-2">{t.description}</p>
                )}
                <div className="flex items-center gap-3 mt-3 text-xs text-gray-400">
                  <span>{t.language === "ur" ? "اردو" : t.language === "both" ? "Bilingual" : "English"}</span>
                  {t.court_type && <span>• {t.court_type}</span>}
                  <span>• Used {t.usage_count} times</span>
                </div>
              </button>
            ))
          )}
        </div>
      )}

      {/* Template Detail View */}
      {selectedTemplate && !showFillForm && (
        <div>
          <button
            onClick={() => setSelectedTemplate(null)}
            className="flex items-center gap-1 text-sm text-gray-500 hover:text-primary-600 mb-4"
          >
            <FiArrowLeft size={14} /> Back to Templates
          </button>

          <div className="card">
            <div className="flex items-start justify-between mb-4">
              <div>
                <span className="badge bg-primary-50 text-primary-700 capitalize mb-2 inline-block">
                  {selectedTemplate.category.replace(/_/g, " ")}
                </span>
                <h2 className="text-xl font-display font-bold">{selectedTemplate.name}</h2>
                {selectedTemplate.description && (
                  <p className="text-gray-500 text-sm mt-1">{selectedTemplate.description}</p>
                )}
              </div>
            </div>

            {selectedTemplate.placeholders.length > 0 && (
              <div className="mb-4">
                <p className="text-sm font-semibold mb-2">Required Fields:</p>
                <div className="flex flex-wrap gap-2">
                  {selectedTemplate.placeholders.map((p) => (
                    <span key={p} className="badge bg-amber-50 text-amber-700">
                      {`{{${p}}}`}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="bg-gray-50 rounded-lg p-4 mb-4 max-h-96 overflow-y-auto">
              <pre className="text-sm whitespace-pre-wrap font-mono" dir={selectedTemplate.language === "ur" ? "rtl" : "ltr"}>
                {selectedTemplate.content}
              </pre>
            </div>

            <div className="flex gap-3">
              <button onClick={startFilling} className="btn-primary flex items-center gap-2">
                <FiFileText size={16} /> Fill & Generate
              </button>
              <button onClick={() => copyToClipboard(selectedTemplate.content)} className="btn-secondary flex items-center gap-2">
                <FiCopy size={16} /> Copy Template
              </button>
              <button
                onClick={() => downloadAsText(selectedTemplate.content, `${selectedTemplate.name}.txt`)}
                className="btn-secondary flex items-center gap-2"
              >
                <FiDownload size={16} /> Download
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Fill Form View */}
      {selectedTemplate && showFillForm && (
        <div>
          <button
            onClick={() => setShowFillForm(false)}
            className="flex items-center gap-1 text-sm text-gray-500 hover:text-primary-600 mb-4"
          >
            <FiArrowLeft size={14} /> Back to Template
          </button>

          <div className="grid lg:grid-cols-2 gap-6">
            {/* Form */}
            <div className="card">
              <h2 className="font-semibold text-lg mb-4">Fill Template: {selectedTemplate.name}</h2>
              <div className="space-y-3 max-h-[500px] overflow-y-auto pr-2">
                {selectedTemplate.placeholders.map((p) => (
                  <div key={p}>
                    <label className="block text-sm font-medium mb-1 capitalize">
                      {p.replace(/_/g, " ")}
                    </label>
                    <input
                      type="text"
                      value={formValues[p] || ""}
                      onChange={(e) => setFormValues({ ...formValues, [p]: e.target.value })}
                      className="input"
                      placeholder={`Enter ${p.replace(/_/g, " ")}...`}
                      dir={selectedTemplate.language === "ur" ? "rtl" : "ltr"}
                    />
                  </div>
                ))}
              </div>
              <button onClick={generateDocument} className="btn-primary w-full mt-4">
                Generate Document
              </button>
            </div>

            {/* Preview */}
            <div className="card">
              <div className="flex items-center justify-between mb-3">
                <h2 className="font-semibold text-lg">Generated Document</h2>
                {generatedDoc && (
                  <div className="flex gap-2">
                    <button onClick={() => copyToClipboard(generatedDoc)} className="btn-secondary text-xs">
                      <FiCopy size={12} className="inline mr-1" /> Copy
                    </button>
                    <button
                      onClick={() => downloadAsText(generatedDoc, `${selectedTemplate.name}_filled.txt`)}
                      className="btn-primary text-xs"
                    >
                      <FiDownload size={12} className="inline mr-1" /> Download
                    </button>
                  </div>
                )}
              </div>
              <div
                className="bg-gray-50 rounded-lg p-4 max-h-[500px] overflow-y-auto"
                dir={selectedTemplate.language === "ur" ? "rtl" : "ltr"}
              >
                {generatedDoc ? (
                  <pre className="text-sm whitespace-pre-wrap font-mono">{generatedDoc}</pre>
                ) : (
                  <p className="text-gray-400 italic text-center py-12">
                    Fill in the fields and click Generate to see the document preview
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
