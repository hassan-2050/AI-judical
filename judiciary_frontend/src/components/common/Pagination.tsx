"use client";

import { FiChevronLeft, FiChevronRight } from "react-icons/fi";
import type { Pagination as PaginationType } from "@/types";

interface Props {
  pagination: PaginationType;
  onPageChange: (page: number) => void;
}

export default function Pagination({ pagination, onPageChange }: Props) {
  const { page, total_pages } = pagination;

  if (total_pages <= 1) return null;

  const pages: (number | string)[] = [];

  if (total_pages <= 7) {
    for (let i = 1; i <= total_pages; i++) pages.push(i);
  } else {
    pages.push(1);
    if (page > 3) pages.push("...");
    for (
      let i = Math.max(2, page - 1);
      i <= Math.min(total_pages - 1, page + 1);
      i++
    ) {
      pages.push(i);
    }
    if (page < total_pages - 2) pages.push("...");
    pages.push(total_pages);
  }

  return (
    <div className="flex items-center justify-center gap-1 mt-6">
      <button
        disabled={page <= 1}
        onClick={() => onPageChange(page - 1)}
        className="p-2 rounded-lg hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed"
      >
        <FiChevronLeft />
      </button>

      {pages.map((p, i) =>
        typeof p === "string" ? (
          <span key={`ellipsis-${i}`} className="px-2 text-gray-400">
            …
          </span>
        ) : (
          <button
            key={p}
            onClick={() => onPageChange(p)}
            className={`min-w-[36px] h-9 rounded-lg text-sm font-medium transition ${
              p === page
                ? "bg-primary-600 text-white"
                : "hover:bg-gray-100 text-gray-700"
            }`}
          >
            {p}
          </button>
        )
      )}

      <button
        disabled={page >= total_pages}
        onClick={() => onPageChange(page + 1)}
        className="p-2 rounded-lg hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed"
      >
        <FiChevronRight />
      </button>
    </div>
  );
}
