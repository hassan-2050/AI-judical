"use client";

import { useState, useEffect, useCallback } from "react";
import { casesAPI } from "@/lib/api";
import CaseCard from "@/components/cases/CaseCard";
import Pagination from "@/components/common/Pagination";
import Loading from "@/components/common/Loading";
import type { CaseCard as CaseCardType, Pagination as PaginationType } from "@/types";
import { FiFilter, FiX } from "react-icons/fi";

export default function CasesPage() {
  const [cases, setCases] = useState<CaseCardType[]>([]);
  const [pagination, setPagination] = useState<PaginationType>({
    page: 1, page_size: 12, total: 0, total_pages: 0,
  });
  const [loading, setLoading] = useState(true);
  const [showFilters, setShowFilters] = useState(false);

  // Filters
  const [court, setCourt] = useState("");
  const [year, setYear] = useState("");
  const [status, setStatus] = useState("");
  const [search, setSearch] = useState("");

  const fetchCases = useCallback(async (page: number) => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = {
        page,
        page_size: 12,
        sort: "-judgment_date",
      };
      if (search) params.search = search;
      if (court) params.court = court;
      if (year) params.year = year;
      if (status) params.status = status;

      const res = await casesAPI.list(params);
      setCases(res.data.cases);
      setPagination(res.data.pagination);
    } catch (err) {
      console.error("Failed to fetch cases:", err);
    } finally {
      setLoading(false);
    }
  }, [search, court, year, status]);

  useEffect(() => {
    fetchCases(1);
  }, [fetchCases]);

  const clearFilters = () => {
    setCourt("");
    setYear("");
    setStatus("");
    setSearch("");
  };

  const hasActiveFilters = court || year || status || search;

  return (
    <div className="page-container">
      <div className="flex items-center justify-between mb-6">
        <h1 className="page-title mb-0">Case Database</h1>
        <button
          className="btn-secondary flex items-center gap-2 text-sm"
          onClick={() => setShowFilters(!showFilters)}
        >
          <FiFilter size={16} />
          Filters
          {hasActiveFilters && (
            <span className="w-2 h-2 bg-primary-600 rounded-full" />
          )}
        </button>
      </div>

      {/* Filters bar */}
      {showFilters && (
        <div className="card mb-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            <input
              className="input"
              placeholder="Search cases..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <input
              className="input"
              placeholder="Court name"
              value={court}
              onChange={(e) => setCourt(e.target.value)}
            />
            <input
              className="input"
              placeholder="Year"
              type="number"
              value={year}
              onChange={(e) => setYear(e.target.value)}
            />
            <select
              className="input"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
            >
              <option value="">All Statuses</option>
              <option value="decided">Decided</option>
              <option value="pending">Pending</option>
              <option value="adjourned">Adjourned</option>
              <option value="disposed">Disposed</option>
            </select>
            {hasActiveFilters && (
              <button
                className="btn-secondary flex items-center justify-center gap-1 text-sm"
                onClick={clearFilters}
              >
                <FiX size={14} /> Clear
              </button>
            )}
          </div>
        </div>
      )}

      {/* Results */}
      {loading ? (
        <Loading text="Loading cases..." />
      ) : cases.length === 0 ? (
        <div className="text-center py-20 text-gray-500">
          <p className="text-lg mb-2">No cases found</p>
          <p className="text-sm">
            Try adjusting your filters or{" "}
            <a href="/scraper" className="text-primary-600 hover:underline">
              run a scraper
            </a>{" "}
            to add data.
          </p>
        </div>
      ) : (
        <>
          <p className="text-sm text-gray-500 mb-4">
            Showing {cases.length} of {pagination.total.toLocaleString()} cases
          </p>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {cases.map((c) => (
              <CaseCard key={c.id} case_data={c} />
            ))}
          </div>
          <Pagination
            pagination={pagination}
            onPageChange={(p) => fetchCases(p)}
          />
        </>
      )}
    </div>
  );
}
