import type {
  QueryWorkflowRequest,
  QueryWorkflowResponse,
} from "./types";

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ??
  "http://127.0.0.1:8000"
).replace(/\/$/, "");

function getErrorMessage(payload: unknown, status: number): string {
  if (
    payload &&
    typeof payload === "object" &&
    "detail" in payload
  ) {
    const detail = (payload as { detail: unknown }).detail;

    if (typeof detail === "string") {
      return detail;
    }
  }

  return `Request failed with status ${status}.`;
}

export async function submitQuery(
  request: QueryWorkflowRequest,
): Promise<QueryWorkflowResponse> {
  const response = await fetch(`${API_BASE_URL}/v1/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  const payload: unknown = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(getErrorMessage(payload, response.status));
  }

  return payload as QueryWorkflowResponse;
}