export type SeverityLevel = "high" | "medium" | "low";

export interface IllegalClause {
  clause_text: string;
  violation_type: string;
  legal_citation: string;
  severity: SeverityLevel;
  remedy: string;
  explanation: string;
}

export interface AnalyzeResponse {
  session_id: string;
  illegal_clauses: IllegalClause[];
  total_clauses_scanned: number;
  risk_score: number;
  summary: string;
}

export interface ChatRequest {
  question: string;
  session_id?: string;
}

export interface ChatResponse {
  answer: string;
  sources: string[];
  citations: string[];
}

export interface DemandLetterRequest {
  session_id: string;
  tenant_name: string;
  tenant_address: string;
  landlord_name: string;
  landlord_address: string;
  illegal_clauses: IllegalClause[];
  remedy_requested: string;
}

export interface DemandLetterResponse {
  letter_text: string;
  generated_at: string;
}

export interface GraphNode {
  id: string;
  label: string;
  type: "clause" | "law" | "remedy";
}

export interface GraphEdge {
  source: string;
  target: string;
  relationship: string;
}

export interface GraphResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
}
