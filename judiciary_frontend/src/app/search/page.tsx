"use client";

import { useState, useEffect, useCallback } from "react";
import { searchAPI } from "@/lib/api";
import CaseCard from "@/components/cases/CaseCard";
import Pagination from "@/components/common/Pagination";
import Loading from "@/components/common/Loading";
import type { CaseCard as CaseCardType, Pagination as PaginationType, SearchFilters } from "@/types";
import { FiSearch, FiSliders, FiX } from "react-icons/fi";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<CaseCardType[]>([]);
  const [pagination, setPagination] = useState<PaginationType>({
    page: 1, page_size: 20, total: 0, total_pages: 0,
  });
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [filters, setFilters] = useState<SearchFilters | null>(null);

  // Advanced filters
  const [court, setCourt] = useState("");
  const [judge, setJudge] = useState("");
  const [yearFrom, setYearFrom] = useState("");
  const [yearTo, setYearTo] = useState("");
  const [caseType, setCaseType] = useState("");
  const [status, setStatus] = useState("");

  // Load available filters
  useEffect(() => {
    searchAPI.filters().then((res) => setFilters(res.data)).catch(() => {});
  }, []);

  const doSearch = useCallback(async (page: number = 1) => {
    setLoading(true);
    setSearched(true);
    try {
      const params: Record<string, unknown> = { page, page_size: 20 };
      if (query) params.q = query;
      if (court) params.court = court;
      if (judge) params.judge = judge;
      if (yearFrom) params.year_from = yearFrom;
      if (yearTo) params.year_to = yearTo;
      if (caseType) params.case_type = caseType;
      if (status) params.status = status;

      const res = await searchAPI.search(params);
      setResults(res.data.results);
      setPagination(res.data.pagination);
    } catch (err) {
      console.error("Search failed:", err);
    } finally {
      setLoading(false);
    }
  }, [query, court, judge, yearFrom, yearTo, caseType, status]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    doSearch(1);
  };

  const clearAll = () => {
    setQuery("");
    setCourt("");
    setJudge("");
    setYearFrom("");
    setYearTo("");
    setCaseType("");
    setStatus("");
    setResults([]);
    setSearched(false);
  };

  return (
    <div className="page-container">
      <h1 className="page-title">Search Cases</h1>

      {/* Search form */}
      <form onSubmit={handleSubmit} className="card mb-6">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <FiSearch
              className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
              size={18}
            />
            <input
              className="input pl-10"
              placeholder="Search by case number, title, keywords..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
          <button type="submit" className="btn-primary">
            Search
          </button>
          <button
            type="button"
            className="btn-secondary"
            onClick={() => setShowAdvanced(!showAdvanced)}
          >
            <FiSliders size={18} />
          </button>
        </div>

        {/* Advanced filters */}
        {showAdvanced && (
          <div className="mt-4 pt-4 border-t">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <div>
                <label className="text-xs text-gray-500 mb-1 block">Court</label>
                <select
                  className="input"
                  value={court}
                  onChange={(e) => setCourt(e.target.value)}
                >
                  <option value="">All Courts</option>
                  {filters?.courts.map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-xs text-gray-500 mb-1 block">Judge</label>
                <input
                  className="input"
                  placeholder="Judge name"
                  value={judge}
                  onChange={(e) => setJudge(e.target.value)}
                />
              </div>
              <div>
                <label className="text-xs text-gray-500 mb-1 block">Case Type</label>
                <select
                  className="input"
                  value={caseType}
                  onChange={(e) => setCaseType(e.target.value)}
                >
                  <option value="">All Types</option>
                  {filters?.case_types.map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-xs text-gray-500 mb-1 block">Year From</label>
                <input
                  className="input"
                  type="number"
                  placeholder={String(filters?.year_range.min || 1947)}
                  value={yearFrom}
                  onChange={(e) => setYearFrom(e.target.value)}
                />
              </div>
              <div>
                <label className="text-xs text-gray-500 mb-1 block">Year To</label>
                <input
                  className="input"
                  type="number"
                  placeholder={String(filters?.year_range.max || new Date().getFullYear())}
                  value={yearTo}
                  onChange={(e) => setYearTo(e.target.value)}
                />
              </div>
              <div>
                <label className="text-xs text-gray-500 mb-1 block">Status</label>
                <select
                  className="input"
                  value={status}
                  onChange={(e) => setStatus(e.target.value)}
                >
                  <option value="">All</option>
                  <option value="decided">Decided</option>
                  <option value="pending">Pending</option>
                  <option value="adjourned">Adjourned</option>
                  <option value="disposed">Disposed</option>
                </select>
              </div>
            </div>
            <div className="flex justify-end mt-4">
              <button
                type="button"
                className="text-sm text-gray-500 hover:text-red-600 flex items-center gap-1"
                onClick={clearAll}
              >
                <FiX size={14} /> Clear all
              </button>
            </div>
          </div>
        )}
      </form>

      {/* Results */}
      {loading ? (
        <Loading text="Searching..." />
      ) : searched && results.length === 0 ? (
        <div className="text-center py-16 text-gray-500">
          <FiSearch size={48} className="mx-auto mb-4 text-gray-300" />
          <p className="text-lg mb-1">No results found</p>
          <p className="text-sm">Try broadening your search or using different keywords.</p>
        </div>
      ) : results.length > 0 ? (
        <>
          <p className="text-sm text-gray-500 mb-4">
            {pagination.total.toLocaleString()} result
            {pagination.total !== 1 ? "s" : ""} found
          </p>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {results.map((c) => (
              <CaseCard key={c.id} case_data={c} />
            ))}
          </div>
          <Pagination
            pagination={pagination}
            onPageChange={(p) => doSearch(p)}
          />
        </>
      ) : (
        <div className="text-center py-16 text-gray-400">
          <FiSearch size={48} className="mx-auto mb-4" />
          <p>Enter a search query to find court cases</p>
        </div>
      )}
    </div>
  );
}
