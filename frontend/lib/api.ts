import type {
  AnalyzeResponse,
  ChatRequest,
  ChatResponse,
  DemandLetterRequest,
  DemandLetterResponse,
  GraphResponse,
} from "./types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const json = await res.json();
      detail = json?.detail ?? detail;
    } catch {
      // ignore
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export async function analyzeLease(file: File): Promise<AnalyzeResponse> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE_URL}/api/v1/analyze`, {
    method: "POST",
    body: form,
  });
  return handleResponse<AnalyzeResponse>(res);
}

export async function chat(payload: ChatRequest): Promise<ChatResponse> {
  const res = await fetch(`${BASE_URL}/api/v1/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handleResponse<ChatResponse>(res);
}

export async function generateLetter(
  payload: DemandLetterRequest
): Promise<DemandLetterResponse> {
  const res = await fetch(`${BASE_URL}/api/v1/letter`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handleResponse<DemandLetterResponse>(res);
}

export async function getGraph(sessionId: string): Promise<GraphResponse> {
  const res = await fetch(`${BASE_URL}/api/v1/graph/${sessionId}`);
  return handleResponse<GraphResponse>(res);
}
