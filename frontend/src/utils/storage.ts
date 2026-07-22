import type { StoredQuery } from "../types";

const HISTORY_KEY = "safequery.queryHistory";

export function getQueryHistory(): StoredQuery[] {
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    return raw ? (JSON.parse(raw) as StoredQuery[]) : [];
  } catch {
    return [];
  }
}

export function saveQueryHistory(item: StoredQuery): void {
  const next = [item, ...getQueryHistory()]
    .filter(
      (query, index, all) =>
        all.findIndex((candidate) => candidate.id === query.id) === index,
    )
    .slice(0, 30);

  localStorage.setItem(HISTORY_KEY, JSON.stringify(next));
}

export function updateQueryFeedback(
  id: string,
  feedback: "correct" | "incorrect",
): void {
  const next = getQueryHistory().map((query) =>
    query.id === id ? { ...query, feedback } : query,
  );

  localStorage.setItem(HISTORY_KEY, JSON.stringify(next));
}

export function clearQueryHistory(): void {
  localStorage.removeItem(HISTORY_KEY);
}