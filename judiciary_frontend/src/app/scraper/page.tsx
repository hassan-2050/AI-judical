"use client";

import { useState, useEffect } from "react";
import { scraperAPI } from "@/lib/api";
import Loading from "@/components/common/Loading";
import type { ScrapeJob } from "@/types";
import toast from "react-hot-toast";
import {
  FiPlay,
  FiRefreshCw,
  FiCheckCircle,
  FiXCircle,
  FiClock,
  FiLoader,
} from "react-icons/fi";

interface ScraperInfo {
  name: string;
  description: string;
}

export default function ScraperPage() {
  const [scrapers, setScrapers] = useState<ScraperInfo[]>([]);
  const [jobs, setJobs] = useState<ScrapeJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState<string | null>(null);
  const [selectedJob, setSelectedJob] = useState<ScrapeJob | null>(null);

  // Scraper run config
  const [maxPages, setMaxPages] = useState(10);

  const load = async () => {
    try {
      const [scraperRes, jobsRes] = await Promise.all([
        scraperAPI.available(),
        scraperAPI.jobs({ page: 1, page_size: 20 }).catch(() => ({ data: { jobs: [] } })),
      ]);
      setScrapers(scraperRes.data.scrapers);
      setJobs(jobsRes.data.jobs || []);
    } catch (err) {
      console.error("Failed to load scraper data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const runScraper = async (name: string) => {
    setRunning(name);
    try {
      const res = await scraperAPI.run({
        scraper: name,
        max_pages: maxPages,
      });
      toast.success(`Scraper "${name}" started! Job ID: ${res.data.job_id}`);
      // Refresh jobs after a delay
      setTimeout(load, 2000);
    } catch (err: unknown) {
      const error = err as { response?: { data?: { error?: string } } };
      toast.error(error.response?.data?.error || "Failed to start scraper");
    } finally {
      setRunning(null);
    }
  };

  const statusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <FiCheckCircle className="text-green-600" />;
      case "failed":
        return <FiXCircle className="text-red-600" />;
      case "running":
        return <FiLoader className="text-blue-600 animate-spin" />;
      case "queued":
        return <FiClock className="text-yellow-600" />;
      default:
        return <FiClock className="text-gray-400" />;
    }
  };

  if (loading) return <Loading text="Loading scraper status..." />;

  return (
    <div className="page-container">
      <h1 className="page-title">Scraper Management</h1>

      {/* Run scrapers */}
      <div className="card mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-lg">Available Scrapers</h2>
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-500">Max pages:</label>
            <input
              type="number"
              className="input w-20"
              min={1}
              max={100}
              value={maxPages}
              onChange={(e) => setMaxPages(Number(e.target.value))}
            />
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-4">
          {scrapers.map((s) => (
            <div
              key={s.name}
              className="border rounded-lg p-4 hover:border-primary-300 transition"
            >
              <h3 className="font-medium capitalize mb-1">
                {s.name.replace(/_/g, " ")}
              </h3>
              <p className="text-xs text-gray-500 mb-3 line-clamp-2">
                {s.description}
              </p>
              <button
                className="btn-primary text-sm w-full flex items-center justify-center gap-2"
                onClick={() => runScraper(s.name)}
                disabled={running === s.name}
              >
                {running === s.name ? (
                  <>
                    <FiLoader className="animate-spin" size={14} /> Running...
                  </>
                ) : (
                  <>
                    <FiPlay size={14} /> Run Now
                  </>
                )}
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Job history */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-lg">Job History</h2>
          <button
            onClick={load}
            className="btn-secondary text-sm flex items-center gap-1"
          >
            <FiRefreshCw size={14} /> Refresh
          </button>
        </div>

        {jobs.length === 0 ? (
          <p className="text-gray-500 text-sm text-center py-8">
            No scraping jobs yet. Run a scraper to get started.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-gray-500">
                  <th className="pb-2 font-medium">Status</th>
                  <th className="pb-2 font-medium">Source</th>
                  <th className="pb-2 font-medium">Found</th>
                  <th className="pb-2 font-medium">New</th>
                  <th className="pb-2 font-medium">Errors</th>
                  <th className="pb-2 font-medium">Started</th>
                  <th className="pb-2 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {jobs.map((job) => (
                  <tr key={job.id} className="hover:bg-gray-50">
                    <td className="py-3">
                      <span className="flex items-center gap-1.5">
                        {statusIcon(job.status)}
                        <span className="capitalize">{job.status}</span>
                      </span>
                    </td>
                    <td className="py-3 capitalize">
                      {job.source.replace(/_/g, " ")}
                    </td>
                    <td className="py-3">{job.cases_found}</td>
                    <td className="py-3 text-green-600 font-medium">{job.cases_new}</td>
                    <td className="py-3">
                      {job.errors_count > 0 ? (
                        <span className="text-red-600">{job.errors_count}</span>
                      ) : (
                        <span className="text-gray-400">0</span>
                      )}
                    </td>
                    <td className="py-3 text-gray-500">
                      {job.started_at
                        ? new Date(job.started_at).toLocaleString()
                        : "—"}
                    </td>
                    <td className="py-3">
                      <button
                        className="text-primary-600 hover:underline text-xs"
                        onClick={() => setSelectedJob(selectedJob?.id === job.id ? null : job)}
                      >
                        {selectedJob?.id === job.id ? "Hide" : "Logs"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Log viewer */}
        {selectedJob && (
          <div className="mt-4 pt-4 border-t">
            <h3 className="font-medium mb-2">
              Logs – {selectedJob.source} ({selectedJob.status})
            </h3>
            <div className="bg-gray-900 text-gray-100 rounded-lg p-4 max-h-64 overflow-y-auto text-xs font-mono">
              {selectedJob.logs.length === 0 ? (
                <p className="text-gray-500">No logs available.</p>
              ) : (
                selectedJob.logs.map((log, i) => (
                  <div key={i} className="mb-1">
                    <span className="text-gray-500">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </span>{" "}
                    <span
                      className={
                        log.level === "error"
                          ? "text-red-400"
                          : log.level === "warning"
                          ? "text-yellow-400"
                          : "text-green-400"
                      }
                    >
                      [{log.level.toUpperCase()}]
                    </span>{" "}
                    {log.message}
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
