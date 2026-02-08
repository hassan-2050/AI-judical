"use client";

import { useState, useEffect } from "react";
import { analyticsAPI } from "@/lib/api";
import Loading from "@/components/common/Loading";
import type { CourtAnalytics, TimelineData } from "@/types";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
  LineChart, Line,
} from "recharts";

const COLORS = [
  "#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6",
  "#ec4899", "#06b6d4", "#84cc16", "#f97316", "#6366f1",
];

export default function AnalyticsPage() {
  const [courts, setCourts] = useState<CourtAnalytics[]>([]);
  const [timeline, setTimeline] = useState<TimelineData[]>([]);
  const [judges, setJudges] = useState<{ name: string; case_count: number }[]>([]);
  const [loading, setLoading] = useState(true);
  const [year, setYear] = useState(new Date().getFullYear());

  useEffect(() => {
    async function load() {
      try {
        const [courtRes, timelineRes, judgeRes] = await Promise.all([
          analyticsAPI.courts(),
          analyticsAPI.timeline(year),
          analyticsAPI.judges(15),
        ]);
        setCourts(courtRes.data.courts);
        setTimeline(timelineRes.data.timeline);
        setJudges(judgeRes.data.judges);
      } catch (err) {
        console.error("Failed to load analytics:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [year]);

  if (loading) return <Loading text="Loading analytics..." />;

  const totalCases = courts.reduce((sum, c) => sum + c.total_cases, 0);

  return (
    <div className="page-container">
      <h1 className="page-title">Analytics</h1>

      {/* Summary row */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
        <div className="card text-center">
          <p className="text-3xl font-bold text-primary-600">
            {totalCases.toLocaleString()}
          </p>
          <p className="text-sm text-gray-500">Total Cases</p>
        </div>
        <div className="card text-center">
          <p className="text-3xl font-bold text-green-600">
            {courts.reduce((s, c) => s + c.decided, 0).toLocaleString()}
          </p>
          <p className="text-sm text-gray-500">Decided</p>
        </div>
        <div className="card text-center">
          <p className="text-3xl font-bold text-yellow-600">
            {courts.reduce((s, c) => s + c.pending, 0).toLocaleString()}
          </p>
          <p className="text-sm text-gray-500">Pending</p>
        </div>
        <div className="card text-center">
          <p className="text-3xl font-bold text-indigo-600">
            {courts.reduce((s, c) => s + (c.enacted ?? 0), 0).toLocaleString()}
          </p>
          <p className="text-sm text-gray-500">Enacted Laws</p>
        </div>
        <div className="card text-center">
          <p className="text-3xl font-bold text-purple-600">{courts.length}</p>
          <p className="text-sm text-gray-500">Courts / Sources</p>
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-6 mb-8">
        {/* Cases by Court - Pie */}
        <div className="card">
          <h2 className="font-semibold text-lg mb-4">Cases by Court</h2>
          {courts.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={courts}
                  dataKey="total_cases"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  label={({ name, percent }) =>
                    `${name.substring(0, 15)} (${(percent * 100).toFixed(0)}%)`
                  }
                  labelLine={false}
                >
                  {courts.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-400 text-center py-12">No data available</p>
          )}
        </div>

        {/* Monthly timeline - Line */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-lg">Cases Timeline</h2>
            <select
              className="input w-28"
              value={year}
              onChange={(e) => setYear(Number(e.target.value))}
            >
              {Array.from({ length: 10 }, (_, i) => new Date().getFullYear() - i).map(
                (y) => (
                  <option key={y} value={y}>
                    {y}
                  </option>
                )
              )}
            </select>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={timeline}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="count"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={{ fill: "#3b82f6" }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Top Judges - Bar */}
      <div className="card mb-8">
        <h2 className="font-semibold text-lg mb-4">Top Judges by Case Count</h2>
        {judges.length > 0 ? (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={judges} layout="vertical" margin={{ left: 150 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis
                type="category"
                dataKey="name"
                tick={{ fontSize: 12 }}
                width={140}
              />
              <Tooltip />
              <Bar dataKey="case_count" fill="#3b82f6" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <p className="text-gray-400 text-center py-12">No judge data available</p>
        )}
      </div>

      {/* Court breakdown table */}
      <div className="card">
        <h2 className="font-semibold text-lg mb-4">Court Breakdown</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-gray-500">
                <th className="pb-2 font-medium">Court / Source</th>
                <th className="pb-2 font-medium text-right">Total</th>
                <th className="pb-2 font-medium text-right">Decided</th>
                <th className="pb-2 font-medium text-right">Pending</th>
                <th className="pb-2 font-medium text-right">Enacted</th>
                <th className="pb-2 font-medium text-right">Adjourned</th>
                <th className="pb-2 font-medium text-right">Disposed</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {courts.map((c) => (
                <tr key={c.name} className="hover:bg-gray-50">
                  <td className="py-2 font-medium">{c.name}</td>
                  <td className="py-2 text-right">{c.total_cases.toLocaleString()}</td>
                  <td className="py-2 text-right text-green-600">
                    {c.decided.toLocaleString()}
                  </td>
                  <td className="py-2 text-right text-yellow-600">
                    {c.pending.toLocaleString()}
                  </td>
                  <td className="py-2 text-right text-indigo-600">
                    {(c.enacted ?? 0).toLocaleString()}
                  </td>
                  <td className="py-2 text-right text-orange-600">
                    {(c.adjourned ?? 0).toLocaleString()}
                  </td>
                  <td className="py-2 text-right text-red-600">
                    {(c.disposed ?? 0).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
