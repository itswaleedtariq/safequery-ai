export type WorkflowStatus =
  | "completed"
  | "clarification_required"
  | "blocked"
  | "review_required";

export type ConfidenceLabel = "high" | "medium" | "low";

export type HallucinationRisk = "low" | "medium" | "high";

export type MultiQueryStatus =
  | "matched"
  | "mismatched"
  | "not_required"
  | "skipped"
  | "failed";

export interface QueryWorkflowRequest {
  question: string;
  max_tables: number;
  max_examples: number;
  run_multi_query: boolean;
}

export interface WorkflowWarning {
  code: string;
  severity: "info" | "warning" | "error";
  message: string;
}

export interface WorkflowTimings {
  generation_ms: number;
  confidence_pipeline_ms: number;
  total_ms: number;
}

export interface ConfidenceSignal {
  name: string;
  score: number | null;
  configured_weight: number;
  effective_weight: number;
  weighted_score: number;
  available: boolean;
  explanation: string;
}

export interface QueryWorkflowResponse {
  request_id: string;
  status: WorkflowStatus;
  question: string;
  summary: string;

  generated_sql: string | null;
  safe_sql: string | null;

  explanation: string;

  tables_used: string[];
  columns_used: string[];

  result_columns: string[];
  rows: Array<Record<string, unknown>>;
  row_count: number;
  result_hidden: boolean;

  guardrail_allowed: boolean | null;

  confidence_score: number | null;
  confidence_percent: number | null;
  confidence_label: ConfidenceLabel | null;
  manual_review_recommended: boolean;

  confidence_signals: ConfidenceSignal[];
  confidence_reasons: string[];

  hallucination_detected: boolean | null;
  hallucination_risk: HallucinationRisk | null;

  multi_query_status: MultiQueryStatus | null;

  clarification_question: string | null;

  warnings: WorkflowWarning[];

  provider: string | null;
  model: string | null;

  timings: WorkflowTimings;
}