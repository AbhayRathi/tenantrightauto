"use client";

import LeaseUploader from "@/components/LeaseUploader";

export default function HomePage() {
  return (
    <main className="flex flex-col items-center justify-center min-h-screen p-6">
      <div className="w-full max-w-2xl">
        <h1 className="text-3xl font-bold text-center mb-2">
          🏠 Tenant Rights Autopilot
        </h1>
        <p className="text-center text-gray-600 mb-8">
          Upload your SF lease to identify illegal clauses, understand your rights, and
          generate a demand letter — powered by AI and California tenant law.
        </p>
        <LeaseUploader />
      </div>
    </main>
  );
}
