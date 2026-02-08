"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { casesAPI, aiAPI } from "@/lib/api";
import Loading from "@/components/common/Loading";
import { formatDate, statusColor } from "@/lib/utils";
import type { Case, CaseAnalysis, SimilarCase, ExtractedEntity } from "@/types";
import {
  FiArrowLeft,
  FiCalendar,
  FiUser,
  FiBookOpen,
  FiExternalLink,
  FiFileText,
  FiTag,
  FiCpu,
  FiZap,
  FiList,
} from "react-icons/fi";

export default function CaseDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [caseData, setCaseData] = useState<Case | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"summary" | "full" | "references" | "ai-summary" | "entities" | "similar">("summary");
  const [aiSummary, setAiSummary] = useState<string | null>(null);
  const [headnotes, setHeadnotes] = useState<string[]>([]);
  const [entities, setEntities] = useState<Record<string, string[]>>({});
  const [similarCases, setSimilarCases] = useState<SimilarCase[]>([]);
  const [aiLoading, setAiLoading] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const res = await casesAPI.get(id);
        setCaseData(res.data.case);
      } catch (err) {
        console.error("Failed to load case:", err);
      } finally {
        setLoading(false);
      }
    }
    if (id) load();
  }, [id]);

  if (loading) return <Loading text="Loading case details..." />;
  if (!caseData) {
    return (
      <div className="page-container text-center py-20">
        <p className="text-xl text-gray-500 mb-4">Case not found</p>
        <Link href="/cases" className="btn-primary">
          Back to Cases
        </Link>
      </div>
    );
  }

  const tabs = [
    { key: "summary", label: "Summary" },
    { key: "full", label: "Full Text" },
    { key: "references", label: "References" },
    { key: "ai-summary", label: "⚡ AI Summary", icon: <FiCpu size={14} /> },
    { key: "entities", label: "⚡ Entities", icon: <FiList size={14} /> },
    { key: "similar", label: "⚡ Similar Cases", icon: <FiZap size={14} /> },
  ] as const;

  async function loadAiSummary() {
    if (aiSummary) return;
    setAiLoading(true);
    try {
      const res = await aiAPI.summarize(id);
      setAiSummary(res.data.summary);
      setHeadnotes(res.data.headnotes || []);
    } catch {
      setAiSummary("AI summarization is not available for this case (no text content).");
    } finally {
      setAiLoading(false);
    }
  }

  async function loadEntities() {
    if (Object.keys(entities).length > 0) return;
    setAiLoading(true);
    try {
      const res = await aiAPI.extract(id);
      setEntities(res.data.entities || {});
    } catch {
      setEntities({});
    } finally {
      setAiLoading(false);
    }
  }

  async function loadSimilar() {
    if (similarCases.length > 0) return;
    setAiLoading(true);
    try {
      const res = await aiAPI.similar(id, { limit: 10 });
      setSimilarCases(res.data.similar_cases || []);
    } catch {
      setSimilarCases([]);
    } finally {
      setAiLoading(false);
    }
  }

  function handleTabChange(key: string) {
    setActiveTab(key as typeof activeTab);
    if (key === "ai-summary") loadAiSummary();
    if (key === "entities") loadEntities();
    if (key === "similar") loadSimilar();
  }

  return (
    <div className="page-container">
      {/* Back link */}
      <Link
        href="/cases"
        className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-primary-600 mb-4"
      >
        <FiArrowLeft size={14} /> Back to Cases
      </Link>

      {/* Header */}
      <div className="card mb-6">
        <div className="flex flex-wrap items-start justify-between gap-4 mb-4">
          <div>
            <span className="text-sm font-mono text-primary-600 bg-primary-50 px-2 py-0.5 rounded">
              {caseData.case_number}
            </span>
            <span className="ml-2 text-sm text-gray-500">{caseData.court}</span>
          </div>
          {caseData.status && (
            <span className={`badge ${statusColor(caseData.status)}`}>
              {caseData.status}
            </span>
          )}
        </div>

        <h1 className="text-xl sm:text-2xl font-display font-bold mb-4">
          {caseData.title}
        </h1>

        {/* Meta grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          {caseData.judgment_date && (
            <InfoItem
              icon={<FiCalendar size={14} />}
              label="Judgment Date"
              value={formatDate(caseData.judgment_date)}
            />
          )}
          {caseData.case_type && (
            <InfoItem
              icon={<FiBookOpen size={14} />}
              label="Case Type"
              value={caseData.case_type}
            />
          )}
          {caseData.year && (
            <InfoItem
              icon={<FiTag size={14} />}
              label="Year"
              value={String(caseData.year)}
            />
          )}
          {caseData.source && (
            <InfoItem
              icon={<FiFileText size={14} />}
              label="Source"
              value={caseData.source.replace(/_/g, " ")}
            />
          )}
        </div>

        {/* Judges */}
        {caseData.judge_names && caseData.judge_names.length > 0 && (
          <div className="mt-4 pt-4 border-t">
            <p className="text-xs text-gray-500 mb-2 flex items-center gap-1">
              <FiUser size={12} /> Judges
            </p>
            <div className="flex flex-wrap gap-2">
              {caseData.judge_names.map((j) => (
                <span key={j} className="badge bg-blue-50 text-blue-700">
                  {j}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Parties */}
        <div className="grid md:grid-cols-2 gap-4 mt-4 pt-4 border-t">
          {caseData.appellants && caseData.appellants.length > 0 && (
            <div>
              <p className="text-xs text-gray-500 mb-1">Appellants</p>
              {caseData.appellants.map((a) => (
                <p key={a} className="text-sm font-medium">{a}</p>
              ))}
            </div>
          )}
          {caseData.respondents && caseData.respondents.length > 0 && (
            <div>
              <p className="text-xs text-gray-500 mb-1">Respondents</p>
              {caseData.respondents.map((r) => (
                <p key={r} className="text-sm font-medium">{r}</p>
              ))}
            </div>
          )}
        </div>

        {/* External links */}
        <div className="flex gap-3 mt-4 pt-4 border-t">
          {caseData.source_url && (
            <a
              href={caseData.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-secondary text-sm flex items-center gap-1"
            >
              <FiExternalLink size={14} /> Source
            </a>
          )}
          {caseData.pdf_url && (
            <a
              href={caseData.pdf_url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-primary text-sm flex items-center gap-1"
            >
              <FiFileText size={14} /> PDF
            </a>
          )}
        </div>
      </div>

      {/* Content tabs */}
      <div className="card">
        <div className="flex border-b mb-4 -mt-2 overflow-x-auto">
          {tabs.map((t) => (
            <button
              key={t.key}
              onClick={() => handleTabChange(t.key)}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition whitespace-nowrap flex items-center gap-1 ${
                activeTab === t.key
                  ? "border-primary-600 text-primary-600"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {activeTab === "summary" && (
          <div className="prose prose-sm max-w-none">
            {caseData.summary ? (
              <p className="whitespace-pre-wrap">{caseData.summary}</p>
            ) : (
              <p className="text-gray-400 italic">No summary available.</p>
            )}
            {caseData.headnotes && (
              <>
                <h3 className="text-lg font-semibold mt-6 mb-2">Headnotes</h3>
                <p className="whitespace-pre-wrap">{caseData.headnotes}</p>
              </>
            )}
          </div>
        )}

        {activeTab === "full" && (
          <div className="prose prose-sm max-w-none">
            {caseData.full_text || caseData.judgment_text ? (
              <p className="whitespace-pre-wrap text-sm leading-relaxed">
                {caseData.full_text || caseData.judgment_text}
              </p>
            ) : (
              <p className="text-gray-400 italic">
                Full text not available. Check the source link for the original document.
              </p>
            )}
          </div>
        )}

        {activeTab === "references" && (
          <div className="space-y-6">
            {caseData.cited_cases && caseData.cited_cases.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold mb-2">Cited Cases</h3>
                <div className="flex flex-wrap gap-2">
                  {caseData.cited_cases.map((c) => (
                    <span key={c} className="badge bg-purple-50 text-purple-700">
                      {c}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {caseData.cited_statutes && caseData.cited_statutes.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold mb-2">Cited Statutes</h3>
                <div className="flex flex-wrap gap-2">
                  {caseData.cited_statutes.map((s) => (
                    <span key={s} className="badge bg-green-50 text-green-700">
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {caseData.cited_articles && caseData.cited_articles.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold mb-2">Cited Articles</h3>
                <div className="flex flex-wrap gap-2">
                  {caseData.cited_articles.map((a) => (
                    <span key={a} className="badge bg-orange-50 text-orange-700">
                      {a}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {(!caseData.cited_cases?.length &&
              !caseData.cited_statutes?.length &&
              !caseData.cited_articles?.length) && (
              <p className="text-gray-400 italic">No references available.</p>
            )}
          </div>
        )}

        {/* AI Summary Tab */}
        {activeTab === "ai-summary" && (
          <div>
            {aiLoading ? (
              <div className="text-center py-8">
                <div className="animate-spin w-8 h-8 border-2 border-primary-600 border-t-transparent rounded-full mx-auto mb-3" />
                <p className="text-gray-500 text-sm">Generating AI summary...</p>
              </div>
            ) : (
              <div className="prose prose-sm max-w-none">
                {aiSummary && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                    <h3 className="text-sm font-semibold text-blue-800 mb-2 flex items-center gap-1">
                      <FiCpu size={14} /> AI-Generated Summary
                    </h3>
                    <p className="whitespace-pre-wrap text-sm text-gray-700">{aiSummary}</p>
                  </div>
                )}
                {headnotes.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold mb-2">Key Headnotes</h3>
                    <ul className="space-y-1">
                      {headnotes.map((h, i) => (
                        <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                          <span className="text-primary-600 mt-1">•</span> {h}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Entities Tab */}
        {activeTab === "entities" && (
          <div>
            {aiLoading ? (
              <div className="text-center py-8">
                <div className="animate-spin w-8 h-8 border-2 border-primary-600 border-t-transparent rounded-full mx-auto mb-3" />
                <p className="text-gray-500 text-sm">Extracting entities...</p>
              </div>
            ) : Object.keys(entities).length === 0 ? (
              <p className="text-gray-400 italic py-4">No entities could be extracted from this case.</p>
            ) : (
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {Object.entries(entities).map(([type, values]) => (
                  <div key={type} className="bg-gray-50 rounded-lg p-3">
                    <p className="text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wider">{type.replace(/_/g, " ")}</p>
                    <div className="flex flex-wrap gap-1">
                      {(values as string[]).map((v, i) => (
                        <span key={i} className="badge bg-white border text-gray-700 text-xs">{v}</span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Similar Cases Tab */}
        {activeTab === "similar" && (
          <div>
            {aiLoading ? (
              <div className="text-center py-8">
                <div className="animate-spin w-8 h-8 border-2 border-primary-600 border-t-transparent rounded-full mx-auto mb-3" />
                <p className="text-gray-500 text-sm">Finding similar cases...</p>
              </div>
            ) : similarCases.length === 0 ? (
              <p className="text-gray-400 italic py-4">No similar cases found.</p>
            ) : (
              <div className="space-y-3">
                {similarCases.map((sc) => (
                  <Link
                    key={sc.id}
                    href={`/cases/${sc.id}`}
                    className="block p-3 bg-gray-50 rounded-lg hover:bg-primary-50 transition"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <p className="font-medium text-sm truncate">{sc.title}</p>
                        <p className="text-xs text-gray-500 mt-0.5">
                          {sc.case_number} • {sc.court}
                          {sc.year ? ` • ${sc.year}` : ""}
                        </p>
                      </div>
                      <span className="badge bg-primary-50 text-primary-700 flex-shrink-0">
                        {(sc.similarity * 100).toFixed(0)}% match
                      </span>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function InfoItem({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div>
      <p className="text-xs text-gray-500 flex items-center gap-1 mb-0.5">
        {icon} {label}
      </p>
      <p className="font-medium">{value}</p>
    </div>
  );
}
