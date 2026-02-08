"use client";

import { useState, useEffect } from "react";
import { analyticsAPI, casesAPI } from "@/lib/api";
import Loading from "@/components/common/Loading";
import Link from "next/link";
import type { DashboardStats, CaseCard as CaseCardType } from "@/types";
import {
  FiDatabase,
  FiTrendingUp,
  FiServer,
  FiCheckCircle,
  FiAlertTriangle,
  FiClock,
} from "react-icons/fi";

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentCases, setRecentCases] = useState<CaseCardType[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [statsRes, casesRes] = await Promise.all([
          analyticsAPI.dashboard(),
          casesAPI.list({ page: 1, page_size: 5, sort: "-created_at" }),
        ]);
        setStats(statsRes.data);
        setRecentCases(casesRes.data.cases);
      } catch (err) {
        console.error("Failed to load dashboard:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) return <Loading text="Loading dashboard..." />;

  return (
    <div className="page-container">
      <h1 className="page-title">Dashboard</h1>

      {/* Stats cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard
          icon={<FiDatabase className="text-primary-600" size={24} />}
          label="Total Cases"
          value={stats?.total_cases ?? 0}
        />
        <StatCard
          icon={<FiTrendingUp className="text-green-600" size={24} />}
          label="New (30 Days)"
          value={stats?.recent_cases_30d ?? 0}
        />
        <StatCard
          icon={<FiServer className="text-purple-600" size={24} />}
          label="Courts Covered"
          value={stats?.total_courts ?? 0}
        />
        <StatCard
          icon={<FiCheckCircle className="text-blue-600" size={24} />}
          label="Scrape Jobs"
          value={stats?.scraper?.completed_jobs ?? 0}
        />
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Recent cases */}
        <div className="lg:col-span-2 card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-lg">Recent Cases</h2>
            <Link href="/cases" className="text-sm text-primary-600 hover:underline">
              View all →
            </Link>
          </div>
          {recentCases.length === 0 ? (
            <p className="text-gray-500 text-sm py-8 text-center">
              No cases yet. Start a scraper to populate the database.
            </p>
          ) : (
            <div className="divide-y">
              {recentCases.map((c) => (
                <Link
                  key={c.id}
                  href={`/cases/${c.id}`}
                  className="block py-3 hover:bg-gray-50 -mx-2 px-2 rounded-lg transition"
                >
                  <div className="flex justify-between items-start gap-2">
                    <div>
                      <span className="text-xs font-mono text-primary-600">
                        {c.case_number}
                      </span>
                      <p className="text-sm font-medium mt-0.5 line-clamp-1">
                        {c.title}
                      </p>
                    </div>
                    <span className="text-xs text-gray-400 whitespace-nowrap">
                      {c.court}
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Scraper status */}
        <div className="card">
          <h2 className="font-semibold text-lg mb-4">Scraper Status</h2>
          {stats?.scraper ? (
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Total Jobs</span>
                <span className="font-medium">{stats.scraper.total_jobs}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="flex items-center gap-1 text-green-600">
                  <FiCheckCircle size={14} /> Completed
                </span>
                <span className="font-medium">{stats.scraper.completed_jobs}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="flex items-center gap-1 text-red-600">
                  <FiAlertTriangle size={14} /> Failed
                </span>
                <span className="font-medium">{stats.scraper.failed_jobs}</span>
              </div>

              {stats.scraper.latest_job && (
                <div className="mt-4 pt-4 border-t">
                  <p className="text-xs text-gray-500 mb-1">Latest Job</p>
                  <p className="text-sm font-medium">{stats.scraper.latest_job.source}</p>
                  <p className="text-xs text-gray-500 flex items-center gap-1 mt-1">
                    <FiClock size={12} />
                    {stats.scraper.latest_job.started_at
                      ? new Date(stats.scraper.latest_job.started_at).toLocaleString()
                      : "N/A"}
                  </p>
                  <p className="text-xs mt-1">
                    Cases found: {stats.scraper.latest_job.cases_found} | New:{" "}
                    {stats.scraper.latest_job.cases_new}
                  </p>
                </div>
              )}

              <Link
                href="/scraper"
                className="block text-center btn-primary text-sm mt-4"
              >
                Manage Scrapers
              </Link>
            </div>
          ) : (
            <p className="text-gray-500 text-sm">No scraper data available.</p>
          )}
        </div>
      </div>

      {/* Cases by source */}
      {stats?.cases_by_source && stats.cases_by_source.length > 0 && (
        <div className="card mt-6">
          <h2 className="font-semibold text-lg mb-4">Cases by Source</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {stats.cases_by_source.map((s) => (
              <div key={s.source} className="text-center p-3 bg-gray-50 rounded-lg">
                <p className="text-2xl font-bold text-primary-600">{s.count.toLocaleString()}</p>
                <p className="text-xs text-gray-500 mt-1 capitalize">
                  {s.source.replace(/_/g, " ")}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
}) {
  return (
    <div className="card flex items-center gap-4">
      <div className="p-3 rounded-lg bg-gray-50">{icon}</div>
      <div>
        <p className="text-2xl font-bold">{value.toLocaleString()}</p>
        <p className="text-sm text-gray-500">{label}</p>
      </div>
    </div>
  );
}
