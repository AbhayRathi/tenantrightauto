"use client";

import { useState, useRef, useEffect } from "react";
import { chat } from "@/lib/api";
import type { ChatResponse } from "@/lib/types";

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: string[];
  citations?: string[];
}

const SUGGESTED_QUESTIONS = [
  "Can my landlord raise my rent?",
  "What notice is required for entry?",
  "How do I get my deposit back?",
  "What are just cause eviction protections?",
  "Can my landlord retaliate against me?",
];

interface Props {
  sessionId?: string;
}

export default function RightsChat({ sessionId }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (question: string) => {
    if (!question.trim() || loading) return;
    const userMsg: Message = { role: "user", content: question };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);
    try {
      const res: ChatResponse = await chat({ question, session_id: sessionId });
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: res.answer,
          sources: res.sources,
          citations: res.citations,
        },
      ]);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "An error occurred.";
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `⚠️ Error: ${msg}` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[600px] bg-white border border-gray-200 rounded-xl overflow-hidden">
      {/* Message area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center py-8">
            <p className="text-gray-500 mb-4">Ask a question about your tenant rights in San Francisco</p>
            <div className="flex flex-wrap gap-2 justify-center">
              {SUGGESTED_QUESTIONS.map((q) => (
                <button
                  key={q}
                  onClick={() => sendMessage(q)}
                  className="bg-gray-100 hover:bg-blue-50 hover:text-blue-700 border border-gray-200 px-3 py-1.5 rounded-full text-sm transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[80%] rounded-xl px-4 py-3 text-sm ${
                msg.role === "user"
                  ? "bg-blue-600 text-white"
                  : "bg-gray-100 text-gray-800"
              }`}
            >
              <p className="whitespace-pre-wrap">{msg.content}</p>

              {/* Sources */}
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-2 pt-2 border-t border-gray-200 space-y-0.5">
                  <p className="text-xs font-semibold text-gray-500">Sources:</p>
                  {msg.sources.map((src) => (
                    <a
                      key={src}
                      href={src}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block text-xs text-blue-600 hover:underline truncate"
                    >
                      {src}
                    </a>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Loading skeleton */}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-xl px-4 py-3 max-w-[80%]">
              <div className="flex gap-1 items-center h-4">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0ms]" />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:150ms]" />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:300ms]" />
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div className="border-t border-gray-200 p-3 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage(input)}
          placeholder="Ask about your tenant rights…"
          maxLength={1000}
          disabled={loading}
          className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
        />
        <button
          onClick={() => sendMessage(input)}
          disabled={!input.trim() || loading}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
        >
          Send
        </button>
      </div>
    </div>
  );
}
