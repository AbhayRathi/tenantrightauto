"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import type { AnalyzeResponse, IllegalClause } from "@/lib/types";
import ClauseAnalysis from "@/components/ClauseAnalysis";
import RightsChat from "@/components/RightsChat";
import DemandLetter from "@/components/DemandLetter";
import Neo4jGraph from "@/components/Neo4jGraph";

type Tab = "clauses" | "chat" | "letter" | "graph";

function RiskBadge({ score }: { score: number }) {
  const color =
    score < 30
      ? "bg-green-100 text-green-800 border-green-300"
      : score <= 70
      ? "bg-yellow-100 text-yellow-800 border-yellow-300"
      : "bg-red-100 text-red-800 border-red-300";
  const label = score < 30 ? "Low Risk" : score <= 70 ? "Medium Risk" : "High Risk";
  return (
    <span className={`border px-3 py-1 rounded-full text-sm font-semibold ${color}`}>
      {label} ({score}/100)
    </span>
  );
}

export default function AnalyzePage() {
  const router = useRouter();
  // Read sessionStorage synchronously via lazy initializer — no effect needed for state
  const [data] = useState<AnalyzeResponse | null>(() => {
    if (typeof window === "undefined") return null;
    const raw = sessionStorage.getItem("analyzeResult");
    if (!raw) return null;
    try {
      return JSON.parse(raw) as AnalyzeResponse;
    } catch {
      return null;
    }
  });
  const [selectedClauses, setSelectedClauses] = useState<IllegalClause[]>([]);
  const [activeTab, setActiveTab] = useState<Tab>("clauses");

  // Side-effect only: redirect when there is no data to show
  useEffect(() => {
    if (!data) {
      router.replace("/");
    }
  }, [data, router]);

  if (!data) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-gray-500">Loading…</p>
      </div>
    );
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: "clauses", label: "⚠️ Clause Analysis" },
    { id: "chat", label: "💬 Rights Chat" },
    { id: "letter", label: "📝 Demand Letter" },
    { id: "graph", label: "🕸️ Knowledge Graph" },
  ];

  return (
    <main className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 flex-wrap">
          <h1 className="text-2xl font-bold">Lease Analysis Results</h1>
          <RiskBadge score={Math.round(data.risk_score)} />
        </div>
        <p className="text-gray-600 mt-1">{data.summary}</p>
        <p className="text-sm text-gray-400 mt-1">
          {data.total_clauses_scanned} clauses scanned &bull; {data.illegal_clauses.length} issues found
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b mb-6 flex-wrap">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.id
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === "clauses" && (
        <ClauseAnalysis
          clauses={data.illegal_clauses}
          selectedClauses={selectedClauses}
          onSelectionChange={setSelectedClauses}
        />
      )}
      {activeTab === "chat" && <RightsChat sessionId={data.session_id} />}
      {activeTab === "letter" && (
        <DemandLetter
          sessionId={data.session_id}
          selectedClauses={selectedClauses}
        />
      )}
      {activeTab === "graph" && <Neo4jGraph sessionId={data.session_id} />}
    </main>
  );
}
