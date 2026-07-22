import { Clock3, Trash2 } from "lucide-react";
import { useMemo, useState } from "react";
import type { StoredQuery } from "../types";
import {
  clearQueryHistory,
  getQueryHistory,
} from "../utils/storage";

function formatDate(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function HistoryPage() {
  const [history, setHistory] = useState<StoredQuery[]>(getQueryHistory);

  const hasHistory = useMemo(() => history.length > 0, [history]);

  function clearAll() {
    clearQueryHistory();
    setHistory([]);
  }

  return (
    <main>
      <section className="page-hero page-hero-compact">
        <div className="container">
          <p className="eyebrow">QUERY HISTORY</p>
          <div className="history-heading">
            <div>
              <h1>Recent analysis</h1>
              <p>
                Review the latest questions, confidence scores, and
                locally stored feedback.
              </p>
            </div>

            {hasHistory && (
              <button
                type="button"
                className="button button-secondary"
                onClick={clearAll}
              >
                <Trash2 size={16} />
                Clear history
              </button>
            )}
          </div>
        </div>
      </section>

      <section className="section section-tight">
        <div className="container">
          {!hasHistory ? (
            <div className="empty-history">
              <Clock3 size={24} />
              <h2>No saved queries yet</h2>
              <p>
                Completed workspace requests will appear here on this
                browser.
              </p>
            </div>
          ) : (
            <div className="history-list">
              {history.map((item) => (
                <article key={item.id} className="history-card">
                  <div>
                    <span className={`status-pill status-${item.status}`}>
                      {item.status.replaceAll("_", " ")}
                    </span>
                    <h2>{item.question}</h2>
                    <p>{formatDate(item.createdAt)}</p>
                  </div>

                  <div className="history-metrics">
                    <span>
                      <small>Confidence</small>
                      <strong>
                        {item.confidencePercent === null
                          ? "—"
                          : `${item.confidencePercent.toFixed(1)}%`}
                      </strong>
                    </span>
                    <span>
                      <small>Rows</small>
                      <strong>{item.rowCount}</strong>
                    </span>
                    <span>
                      <small>Feedback</small>
                      <strong>{item.feedback ?? "Not rated"}</strong>
                    </span>
                  </div>

                  {item.generatedSql && (
                    <pre>
                      <code>{item.generatedSql}</code>
                    </pre>
                  )}
                </article>
              ))}
            </div>
          )}
        </div>
      </section>
    </main>
  );
}