"use client";

import { useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import { analyzeLease } from "@/lib/api";

const MAX_SIZE_MB = 10;
const MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024;

export default function LeaseUploader() {
  const router = useRouter();
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState<string>("");

  const validateFile = (f: File): string | null => {
    if (!f.name.toLowerCase().endsWith(".pdf")) {
      return "Only PDF files are accepted.";
    }
    if (f.size > MAX_SIZE_BYTES) {
      return `File is ${(f.size / 1024 / 1024).toFixed(1)} MB — maximum is ${MAX_SIZE_MB} MB.`;
    }
    return null;
  };

  const handleFile = useCallback((f: File) => {
    const err = validateFile(f);
    if (err) {
      setError(err);
      setFile(null);
    } else {
      setError(null);
      setFile(f);
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const dropped = e.dataTransfer.files[0];
      if (dropped) handleFile(dropped);
    },
    [handleFile]
  );

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (selected) handleFile(selected);
  };

  const handleAnalyze = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setProgress("Uploading and extracting text…");
    try {
      setProgress("Analyzing lease with AI…");
      const result = await analyzeLease(file);
      sessionStorage.setItem("analyzeResult", JSON.stringify(result));
      router.push("/analyze");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "An unexpected error occurred.";
      setError(msg);
      setLoading(false);
      setProgress("");
    }
  };

  return (
    <div className="space-y-4">
      {/* Drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-xl p-10 text-center transition-colors cursor-pointer ${
          isDragging ? "border-blue-500 bg-blue-50" : "border-gray-300 bg-white hover:border-blue-400"
        }`}
        onClick={() => document.getElementById("pdf-input")?.click()}
      >
        <input
          id="pdf-input"
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={handleInputChange}
        />
        <div className="text-4xl mb-3">📄</div>
        {file ? (
          <div>
            <p className="font-medium text-gray-800">{file.name}</p>
            <p className="text-sm text-gray-500">
              {(file.size / 1024 / 1024).toFixed(2)} MB
            </p>
          </div>
        ) : (
          <div>
            <p className="text-gray-600 font-medium">Drag &amp; drop your lease PDF here</p>
            <p className="text-gray-400 text-sm mt-1">or click to browse</p>
          </div>
        )}
      </div>

      {/* Warnings / errors */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
          {error}
        </div>
      )}

      {/* Size warning (soft) */}
      {file && file.size > 8 * 1024 * 1024 && !error && (
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-700 px-4 py-3 rounded-lg text-sm">
          ⚠️ Large file ({(file.size / 1024 / 1024).toFixed(1)} MB). Processing may take a moment.
        </div>
      )}

      {/* Progress */}
      {loading && (
        <div className="flex items-center gap-3 text-blue-600 text-sm">
          <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
          <span>{progress}</span>
        </div>
      )}

      {/* Submit */}
      <button
        onClick={handleAnalyze}
        disabled={!file || loading}
        className="w-full py-3 rounded-xl font-semibold text-white transition-colors
          bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
      >
        {loading ? "Analyzing…" : "Analyze Lease"}
      </button>
    </div>
  );
}
