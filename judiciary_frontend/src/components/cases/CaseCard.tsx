"use client";

import Link from "next/link";
import { CaseCard as CaseCardType } from "@/types";
import { formatDate, statusColor, truncate } from "@/lib/utils";
import { FiCalendar, FiUser, FiBookOpen } from "react-icons/fi";

interface Props {
  case_data: CaseCardType;
}

export default function CaseCard({ case_data }: Props) {
  return (
    <Link
      href={`/cases/${case_data.id}`}
      className="card hover:shadow-md hover:border-primary-200 transition group"
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2 mb-3">
        <div>
          <span className="text-xs font-mono text-primary-600 bg-primary-50 px-2 py-0.5 rounded">
            {case_data.case_number}
          </span>
          {case_data.court && (
            <span className="ml-2 text-xs text-gray-500">
              {case_data.court}
            </span>
          )}
        </div>
        {case_data.status && (
          <span className={`badge ${statusColor(case_data.status)}`}>
            {case_data.status}
          </span>
        )}
      </div>

      {/* Title */}
      <h3 className="font-semibold text-gray-900 group-hover:text-primary-600 transition mb-2 line-clamp-2">
        {case_data.title}
      </h3>

      {/* Summary */}
      {case_data.summary && (
        <p className="text-sm text-gray-600 mb-3 line-clamp-3">
          {truncate(case_data.summary, 200)}
        </p>
      )}

      {/* Meta */}
      <div className="flex flex-wrap gap-3 text-xs text-gray-500">
        {case_data.judgment_date && (
          <span className="flex items-center gap-1">
            <FiCalendar size={12} />
            {formatDate(case_data.judgment_date)}
          </span>
        )}
        {case_data.judge_names && case_data.judge_names.length > 0 && (
          <span className="flex items-center gap-1">
            <FiUser size={12} />
            {case_data.judge_names[0]}
            {case_data.judge_names.length > 1 &&
              ` +${case_data.judge_names.length - 1}`}
          </span>
        )}
        {case_data.case_type && (
          <span className="flex items-center gap-1">
            <FiBookOpen size={12} />
            {case_data.case_type}
          </span>
        )}
        {case_data.year && (
          <span className="text-gray-400">{case_data.year}</span>
        )}
      </div>
    </Link>
  );
}
