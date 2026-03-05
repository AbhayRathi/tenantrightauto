"use client";

import { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import React from "react";
import { getGraph } from "@/lib/api";
import type { GraphResponse } from "@/lib/types";

interface Props {
  sessionId: string;
}

const NODE_COLOR: Record<string, string> = {
  clause: "#ef4444",
  law: "#3b82f6",
  remedy: "#22c55e",
};

export default function Neo4jGraph({ sessionId }: Props) {
  const [data, setData] = useState<GraphResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const rootRef = useRef<any>(null);

  useEffect(() => {
    getGraph(sessionId)
      .then(setData)
      .catch((err: unknown) => {
        const msg = err instanceof Error ? err.message : "Failed to load graph.";
        setError(msg);
      })
      .finally(() => setLoading(false));
  }, [sessionId]);

  useEffect(() => {
    if (!data || data.nodes.length === 0 || !containerRef.current) return;

    const container = containerRef.current;

    import("react-force-graph").then(({ ForceGraph2D }) => {
      const graphData = {
        nodes: data.nodes.map((n) => ({ ...n, color: NODE_COLOR[n.type] ?? "#888" })),
        links: data.edges.map((e) => ({
          source: e.source,
          target: e.target,
          label: e.relationship,
        })),
      };

      const root = createRoot(container);
      rootRef.current = root;

      root.render(
        React.createElement(ForceGraph2D, {
          graphData,
          nodeLabel: "label",
          nodeColor: "color",
          linkLabel: "label",
          width: container.clientWidth || 700,
          height: 450,
          nodeCanvasObject: (
            node: { x?: number; y?: number; label?: string; color?: string },
            ctx: CanvasRenderingContext2D,
            globalScale: number
          ) => {
            const label = node.label ?? "";
            const fontSize = Math.max(10 / globalScale, 4);
            const x = node.x ?? 0;
            const y = node.y ?? 0;
            ctx.beginPath();
            ctx.arc(x, y, 6, 0, 2 * Math.PI);
            ctx.fillStyle = node.color ?? "#888";
            ctx.fill();
            ctx.font = `${fontSize}px Sans-Serif`;
            ctx.fillStyle = "#333";
            ctx.textAlign = "center";
            ctx.textBaseline = "top";
            const display = label.length > 30 ? label.slice(0, 28) + "…" : label;
            ctx.fillText(display, x, y + 8);
          },
        })
      );
    });

    return () => {
      if (rootRef.current) {
        try {
          rootRef.current.unmount();
        } catch {
          // ignore cleanup error
        }
        rootRef.current = null;
      }
    };
  }, [data]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-48 text-gray-500">
        <div className="w-5 h-5 border-2 border-gray-400 border-t-transparent rounded-full animate-spin mr-2" />
        Loading knowledge graph…
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded-lg text-sm">
        ⚠️ Graph service unavailable: {error}
      </div>
    );
  }

  if (!data || data.nodes.length === 0) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-xl p-8 text-center text-gray-500">
        <p className="text-lg mb-1">🕸️ No graph data</p>
        <p className="text-sm">
          The knowledge graph is unavailable or no violations were stored.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
      <div className="p-3 border-b border-gray-100 flex gap-4 text-xs text-gray-600">
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-red-500 inline-block" /> Clause
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-blue-500 inline-block" /> Law
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-green-500 inline-block" /> Remedy
        </span>
      </div>
      <div ref={containerRef} className="w-full" style={{ height: 450 }} />
    </div>
  );
}
