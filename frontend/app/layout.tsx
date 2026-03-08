import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Tenant Rights Autopilot",
  description: "Analyze your lease, understand your rights, and generate demand letters.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50 text-gray-900">{children}</body>
    </html>
  );
}
