"use client";

import { useState } from "react";
import type { IllegalClause, SeverityLevel } from "@/lib/types";

interface Props {
  clauses: IllegalClause[];
  selectedClauses: IllegalClause[];
  onSelectionChange: (clauses: IllegalClause[]) => void;
}

function SeverityBadge({ severity }: { severity: SeverityLevel }) {
  const styles: Record<SeverityLevel, string> = {
    high: "bg-red-100 text-red-800 border-red-300",
    medium: "bg-orange-100 text-orange-800 border-orange-300",
    low: "bg-yellow-100 text-yellow-800 border-yellow-300",
  };
  return (
    <span className={`border px-2 py-0.5 rounded-full text-xs font-semibold uppercase ${styles[severity]}`}>
      {severity}
    </span>
  );
}

export default function ClauseAnalysis({ clauses, selectedClauses, onSelectionChange }: Props) {
  const [expanded, setExpanded] = useState<Set<number>>(new Set());

  const toggle = (i: number) =>
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(i)) {
        next.delete(i);
      } else {
        next.add(i);
      }
      return next;
    });

  const toggleSelect = (clause: IllegalClause) => {
    const idx = selectedClauses.findIndex(
      (c) => c.clause_text === clause.clause_text && c.legal_citation === clause.legal_citation
    );
    if (idx === -1) {
      onSelectionChange([...selectedClauses, clause]);
    } else {
      onSelectionChange(selectedClauses.filter((_, i) => i !== idx));
    }
  };

  const isSelected = (clause: IllegalClause) =>
    selectedClauses.some(
      (c) => c.clause_text === clause.clause_text && c.legal_citation === clause.legal_citation
    );

  if (clauses.length === 0) {
    return (
      <div className="bg-green-50 border border-green-200 rounded-xl p-6 text-center text-green-700">
        <p className="text-lg font-semibold">✅ No illegal clauses detected!</p>
        <p className="text-sm mt-1">Your lease appears to comply with SF and CA tenant law.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-sm text-gray-500">
        Check clauses to include them in your demand letter.
      </p>
      {clauses.map((clause, i) => (
        <div
          key={i}
          className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden"
        >
          {/* Header row */}
          <div className="flex items-center gap-3 p-4">
            <input
              type="checkbox"
              checked={isSelected(clause)}
              onChange={() => toggleSelect(clause)}
              className="w-4 h-4 accent-blue-600 cursor-pointer flex-shrink-0"
              aria-label={`Select clause: ${clause.violation_type}`}
            />
            <button
              onClick={() => toggle(i)}
              className="flex-1 flex items-center justify-between text-left"
            >
              <div className="flex items-center gap-2 flex-wrap">
                <SeverityBadge severity={clause.severity} />
                <span className="font-medium text-gray-800">{clause.violation_type}</span>
                <span className="text-xs text-gray-400">{clause.legal_citation}</span>
              </div>
              <span className="text-gray-400 ml-2">{expanded.has(i) ? "▲" : "▼"}</span>
            </button>
          </div>

          {/* Expanded content */}
          {expanded.has(i) && (
            <div className="border-t border-gray-100 p-4 space-y-3 text-sm">
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                  Clause Text
                </p>
                <blockquote className="bg-gray-50 border-l-4 border-red-400 pl-3 py-2 text-gray-700 italic">
                  {clause.clause_text}
                </blockquote>
              </div>
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                  Explanation
                </p>
                <p className="text-gray-700">{clause.explanation}</p>
              </div>
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                  Your Remedy
                </p>
                <p className="text-green-700 font-medium">{clause.remedy}</p>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
