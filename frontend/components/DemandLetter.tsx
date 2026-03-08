"use client";

import { useState } from "react";
import { generateLetter } from "@/lib/api";
import type { IllegalClause } from "@/lib/types";

interface Props {
  sessionId: string;
  selectedClauses: IllegalClause[];
}

export default function DemandLetter({ sessionId, selectedClauses }: Props) {
  const [tenantName, setTenantName] = useState("");
  const [tenantAddress, setTenantAddress] = useState("");
  const [landlordName, setLandlordName] = useState("");
  const [landlordAddress, setLandlordAddress] = useState("");
  const [remedy, setRemedy] = useState("");
  const [letterText, setLetterText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const handleGenerate = async () => {
    if (selectedClauses.length === 0) {
      setError("Please select at least one illegal clause from the Clause Analysis tab.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const res = await generateLetter({
        session_id: sessionId,
        tenant_name: tenantName,
        tenant_address: tenantAddress,
        landlord_name: landlordName,
        landlord_address: landlordAddress,
        illegal_clauses: selectedClauses,
        remedy_requested: remedy,
      });
      setLetterText(res.letter_text);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "An unexpected error occurred.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(letterText).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const handleDownload = () => {
    const blob = new Blob([letterText], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "demand-letter.txt";
    a.click();
    URL.revokeObjectURL(url);
  };

  const inputClass =
    "w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500";

  return (
    <div className="space-y-6">
      {selectedClauses.length === 0 && (
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded-lg text-sm">
          ⚠️ No clauses selected. Go to the <strong>Clause Analysis</strong> tab and check the clauses you want to dispute.
        </div>
      )}

      {/* Form */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-4">
        <h2 className="font-semibold text-gray-800">Your Information</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="text-xs font-medium text-gray-600 block mb-1">Your Name</label>
            <input
              type="text"
              value={tenantName}
              onChange={(e) => setTenantName(e.target.value)}
              placeholder="Jane Doe"
              className={inputClass}
            />
          </div>
          <div>
            <label className="text-xs font-medium text-gray-600 block mb-1">Your Address</label>
            <input
              type="text"
              value={tenantAddress}
              onChange={(e) => setTenantAddress(e.target.value)}
              placeholder="123 Main St, SF, CA 94102"
              className={inputClass}
            />
          </div>
          <div>
            <label className="text-xs font-medium text-gray-600 block mb-1">Landlord Name</label>
            <input
              type="text"
              value={landlordName}
              onChange={(e) => setLandlordName(e.target.value)}
              placeholder="Bob Smith"
              className={inputClass}
            />
          </div>
          <div>
            <label className="text-xs font-medium text-gray-600 block mb-1">Landlord Address</label>
            <input
              type="text"
              value={landlordAddress}
              onChange={(e) => setLandlordAddress(e.target.value)}
              placeholder="456 Oak Ave, SF, CA 94110"
              className={inputClass}
            />
          </div>
        </div>
        <div>
          <label className="text-xs font-medium text-gray-600 block mb-1">Remedy Requested</label>
          <textarea
            value={remedy}
            onChange={(e) => setRemedy(e.target.value)}
            placeholder="e.g., Remove clause 5 regarding security deposit waiver and confirm in writing."
            rows={3}
            maxLength={2000}
            className={`${inputClass} resize-none`}
          />
        </div>

        <div className="text-sm text-gray-500">
          Selected clauses: <strong>{selectedClauses.length}</strong>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded-lg text-sm">
            {error}
          </div>
        )}

        <button
          onClick={handleGenerate}
          disabled={loading || selectedClauses.length === 0}
          className="w-full py-3 rounded-xl font-semibold text-white bg-blue-600 hover:bg-blue-700
            disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? "Generating…" : "Generate Demand Letter"}
        </button>
      </div>

      {/* Generated letter */}
      {letterText && (
        <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-3">
          <div className="flex items-center justify-between gap-2 flex-wrap">
            <h2 className="font-semibold text-gray-800">Generated Demand Letter</h2>
            <div className="flex gap-2">
              <button
                onClick={handleCopy}
                className="text-sm bg-gray-100 hover:bg-gray-200 px-3 py-1.5 rounded-lg transition-colors"
              >
                {copied ? "✅ Copied!" : "📋 Copy"}
              </button>
              <button
                onClick={handleDownload}
                className="text-sm bg-gray-100 hover:bg-gray-200 px-3 py-1.5 rounded-lg transition-colors"
              >
                ⬇️ Download .txt
              </button>
            </div>
          </div>
          <textarea
            readOnly
            value={letterText}
            rows={20}
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm font-mono bg-gray-50 resize-none focus:outline-none"
          />
        </div>
      )}
    </div>
  );
}
