"use client";

import { useState, useEffect } from "react";
import { lawyersAPI } from "@/lib/api";
import type { LawyerCard, Lawyer, Pagination } from "@/types";
import Loading from "@/components/common/Loading";
import {
  FiUser,
  FiStar,
  FiMapPin,
  FiBriefcase,
  FiCheckCircle,
  FiPhone,
  FiMail,
  FiX,
  FiSearch,
  FiFilter,
} from "react-icons/fi";
import toast from "react-hot-toast";

export default function LawyersPage() {
  const [lawyers, setLawyers] = useState<LawyerCard[]>([]);
  const [pagination, setPagination] = useState<Pagination | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedLawyer, setSelectedLawyer] = useState<Lawyer | null>(null);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [cityFilter, setCityFilter] = useState("");
  const [specFilter, setSpecFilter] = useState("");
  const [cities, setCities] = useState<string[]>([]);
  const [specializations, setSpecializations] = useState<string[]>([]);

  useEffect(() => {
    loadFilters();
  }, []);

  useEffect(() => {
    loadLawyers();
  }, [page, cityFilter, specFilter]);

  async function loadFilters() {
    try {
      const [citiesRes, specsRes] = await Promise.all([
        lawyersAPI.cities(),
        lawyersAPI.specializations(),
      ]);
      setCities(citiesRes.data.cities || []);
      setSpecializations(specsRes.data.specializations || []);
    } catch {}
  }

  async function loadLawyers() {
    setLoading(true);
    try {
      const params: Record<string, unknown> = { page, page_size: 12 };
      if (search) params.q = search;
      if (cityFilter) params.city = cityFilter;
      if (specFilter) params.specialization = specFilter;
      const res = await lawyersAPI.list(params);
      setLawyers(res.data.lawyers || []);
      setPagination(res.data.pagination);
    } catch {
      toast.error("Failed to load lawyers");
    } finally {
      setLoading(false);
    }
  }

  async function viewLawyer(id: string) {
    try {
      const res = await lawyersAPI.get(id);
      setSelectedLawyer(res.data.lawyer);
    } catch {
      toast.error("Failed to load lawyer details");
    }
  }

  function handleSearch() {
    setPage(1);
    loadLawyers();
  }

  function renderStars(rating: number) {
    return (
      <div className="flex items-center gap-0.5">
        {[1, 2, 3, 4, 5].map((star) => (
          <FiStar
            key={star}
            size={14}
            className={star <= Math.round(rating) ? "text-yellow-500 fill-yellow-500" : "text-gray-300"}
          />
        ))}
      </div>
    );
  }

  if (loading && lawyers.length === 0) return <Loading text="Loading lawyer directory..." />;

  return (
    <div className="page-container">
      <h1 className="page-title">
        <FiBriefcase className="inline mr-2 text-primary-600" />
        Lawyer Directory
      </h1>
      <p className="text-gray-500 -mt-4 mb-8">
        Find verified legal professionals across Pakistan
      </p>

      {/* Search & Filters */}
      <div className="card mb-6">
        <div className="flex flex-wrap gap-3">
          <div className="flex-1 min-w-[200px] relative">
            <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              placeholder="Search by name..."
              className="input pl-10"
            />
          </div>
          <select
            value={cityFilter}
            onChange={(e) => { setCityFilter(e.target.value); setPage(1); }}
            className="input w-auto"
          >
            <option value="">All Cities</option>
            {cities.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
          <select
            value={specFilter}
            onChange={(e) => { setSpecFilter(e.target.value); setPage(1); }}
            className="input w-auto"
          >
            <option value="">All Specializations</option>
            {specializations.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          <button onClick={handleSearch} className="btn-primary">
            <FiFilter size={16} className="inline mr-1" /> Search
          </button>
        </div>
      </div>

      {/* Lawyers Grid */}
      {lawyers.length === 0 ? (
        <div className="text-center py-20">
          <FiUser className="mx-auto text-gray-300 mb-4" size={48} />
          <p className="text-gray-500 text-lg">No lawyers found</p>
          <p className="text-gray-400 text-sm">Try adjusting your search filters</p>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {lawyers.map((l) => (
            <button
              key={l.id}
              onClick={() => viewLawyer(l.id)}
              className="card text-left hover:shadow-md hover:border-primary-200 transition"
            >
              <div className="flex items-start gap-3 mb-3">
                <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center flex-shrink-0">
                  <FiUser className="text-primary-600" size={20} />
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-1">
                    <h3 className="font-semibold truncate">{l.name}</h3>
                    {l.is_verified && <FiCheckCircle className="text-blue-500 flex-shrink-0" size={14} />}
                  </div>
                  {l.title && <p className="text-xs text-gray-500">{l.title}</p>}
                </div>
              </div>

              <div className="space-y-1.5 text-sm text-gray-600 mb-3">
                {l.city && (
                  <p className="flex items-center gap-1.5">
                    <FiMapPin size={12} className="text-gray-400" />
                    {l.city}
                  </p>
                )}
                {l.court && (
                  <p className="flex items-center gap-1.5">
                    <FiBriefcase size={12} className="text-gray-400" />
                    {l.court}
                  </p>
                )}
                {l.experience_years && (
                  <p className="text-xs text-gray-500">
                    {l.experience_years} years experience
                  </p>
                )}
              </div>

              {l.specializations.length > 0 && (
                <div className="flex flex-wrap gap-1 mb-3">
                  {l.specializations.map((s) => (
                    <span key={s} className="badge bg-primary-50 text-primary-700 text-[10px]">
                      {s}
                    </span>
                  ))}
                </div>
              )}

              <div className="flex items-center justify-between pt-2 border-t">
                <div className="flex items-center gap-1">
                  {renderStars(l.avg_rating)}
                  <span className="text-xs text-gray-500 ml-1">
                    {l.avg_rating.toFixed(1)} ({l.total_reviews})
                  </span>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Pagination */}
      {pagination && pagination.total_pages > 1 && (
        <div className="flex justify-center gap-2 mt-6">
          {Array.from({ length: pagination.total_pages }, (_, i) => i + 1).map((p) => (
            <button
              key={p}
              onClick={() => setPage(p)}
              className={`px-3 py-1 rounded text-sm ${
                p === page ? "bg-primary-600 text-white" : "bg-white border hover:bg-gray-50"
              }`}
            >
              {p}
            </button>
          ))}
        </div>
      )}

      {/* Lawyer Detail Modal */}
      {selectedLawyer && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg max-h-[80vh] overflow-y-auto m-4 p-6">
            <div className="flex justify-between items-start mb-4">
              <div className="flex items-center gap-3">
                <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center">
                  <FiUser className="text-primary-600" size={28} />
                </div>
                <div>
                  <div className="flex items-center gap-1">
                    <h2 className="text-xl font-bold">{selectedLawyer.name}</h2>
                    {selectedLawyer.is_verified && <FiCheckCircle className="text-blue-500" size={16} />}
                  </div>
                  {selectedLawyer.title && <p className="text-gray-500">{selectedLawyer.title}</p>}
                </div>
              </div>
              <button onClick={() => setSelectedLawyer(null)}><FiX size={20} /></button>
            </div>

            <div className="space-y-3">
              {selectedLawyer.city && (
                <p className="flex items-center gap-2 text-sm">
                  <FiMapPin className="text-gray-400" size={14} />
                  {selectedLawyer.city}{selectedLawyer.province ? `, ${selectedLawyer.province}` : ""}
                </p>
              )}
              {selectedLawyer.court && (
                <p className="flex items-center gap-2 text-sm">
                  <FiBriefcase className="text-gray-400" size={14} />
                  {selectedLawyer.court}
                </p>
              )}
              {selectedLawyer.email && (
                <p className="flex items-center gap-2 text-sm">
                  <FiMail className="text-gray-400" size={14} />
                  <a href={`mailto:${selectedLawyer.email}`} className="text-primary-600 hover:underline">
                    {selectedLawyer.email}
                  </a>
                </p>
              )}
              {selectedLawyer.phone && (
                <p className="flex items-center gap-2 text-sm">
                  <FiPhone className="text-gray-400" size={14} />
                  {selectedLawyer.phone}
                </p>
              )}
            </div>

            {selectedLawyer.bio && (
              <div className="mt-4 pt-4 border-t">
                <h3 className="text-sm font-semibold mb-1">About</h3>
                <p className="text-sm text-gray-600">{selectedLawyer.bio}</p>
              </div>
            )}

            <div className="mt-4 pt-4 border-t">
              <h3 className="text-sm font-semibold mb-2">Details</h3>
              <div className="grid grid-cols-2 gap-3 text-sm">
                {selectedLawyer.bar_council && (
                  <div>
                    <p className="text-gray-400 text-xs">Bar Council</p>
                    <p className="font-medium">{selectedLawyer.bar_council}</p>
                  </div>
                )}
                {selectedLawyer.experience_years && (
                  <div>
                    <p className="text-gray-400 text-xs">Experience</p>
                    <p className="font-medium">{selectedLawyer.experience_years} years</p>
                  </div>
                )}
                {selectedLawyer.languages && (
                  <div>
                    <p className="text-gray-400 text-xs">Languages</p>
                    <p className="font-medium">{selectedLawyer.languages.join(", ")}</p>
                  </div>
                )}
              </div>
            </div>

            {selectedLawyer.specializations.length > 0 && (
              <div className="mt-4 pt-4 border-t">
                <h3 className="text-sm font-semibold mb-2">Specializations</h3>
                <div className="flex flex-wrap gap-2">
                  {selectedLawyer.specializations.map((s) => (
                    <span key={s} className="badge bg-primary-50 text-primary-700">{s}</span>
                  ))}
                </div>
              </div>
            )}

            <div className="mt-4 pt-4 border-t flex items-center gap-2">
              {renderStars(selectedLawyer.avg_rating)}
              <span className="text-sm text-gray-500">
                {selectedLawyer.avg_rating.toFixed(1)} ({selectedLawyer.total_reviews} reviews)
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
