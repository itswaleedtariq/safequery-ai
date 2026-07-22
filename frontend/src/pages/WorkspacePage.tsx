import {
  Check,
  Clipboard,
  Database,
  LoaderCircle,
  RotateCcw,
  ShieldCheck,
  ThumbsDown,
  ThumbsUp,
} from "lucide-react";
import { useMemo, useState, type FormEvent } from "react";

import { submitQuery } from "../api";
import type {
  ConfidenceSignal,
  QueryWorkflowResponse,
  WorkflowWarning,
} from "../types";
import {
  saveQueryHistory,
  updateQueryFeedback,
} from "../utils/storage";

const EXAMPLES = [
  "How many customers are there?",
  "Which five products generated the highest revenue?",
  "Show the total number of completed orders.",
  "What is the average order value?",
];

function formatLabel(value: string): string {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) {
    return "NULL";
  }

  return typeof value === "object"
    ? JSON.stringify(value)
    : String(value);
}

function ConfidenceSignalCard({
  signal,
}: {
  signal: ConfidenceSignal;
}) {
  const percentage =
    signal.score === null ? 0 : Math.round(signal.score * 100);

  return (
    <article className="signal-card">
      <div>
        <strong>{formatLabel(signal.name)}</strong>
        <span>{signal.available ? `${percentage}%` : "Not used"}</span>
      </div>
      <div className="progress-track">
        <span style={{ width: `${percentage}%` }} />
      </div>
      <p>{signal.explanation}</p>
    </article>
  );
}

function WarningRow({ warning }: { warning: WorkflowWarning }) {
  return (
    <article className={`warning-row warning-${warning.severity}`}>
      <div>
        <strong>{formatLabel(warning.code)}</strong>
        <span>{warning.severity}</span>
      </div>
      <p>{warning.message}</p>
    </article>
  );
}

export function WorkspacePage() {
  const [question, setQuestion] = useState(EXAMPLES[0]);
  const [runMultiQuery, setRunMultiQuery] = useState(false);
  const [response, setResponse] =
    useState<QueryWorkflowResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] =
    useState<"correct" | "incorrect" | null>(null);

  const confidenceSignals = useMemo(
    () => response?.confidence_signals ?? [],
    [response],
  );

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = question.trim();

    if (!trimmed) {
      setError("Enter a business question.");
      return;
    }

    setLoading(true);
    setError("");
    setResponse(null);
    setFeedback(null);

    try {
      const result = await submitQuery({
        question: trimmed,
        max_tables: 4,
        max_examples: 3,
        run_multi_query: runMultiQuery,
      });

      setResponse(result);

      saveQueryHistory({
        id: result.request_id,
        question: result.question,
        createdAt: new Date().toISOString(),
        status: result.status,
        confidencePercent: result.confidence_percent,
        rowCount: result.row_count,
        generatedSql: result.safe_sql ?? result.generated_sql,
      });
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "The request could not be completed.",
      );
    } finally {
      setLoading(false);
    }
  }

  async function copySql() {
    const sql = response?.safe_sql ?? response?.generated_sql;
    if (!sql) return;

    await navigator.clipboard.writeText(sql);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1500);
  }

  function recordFeedback(value: "correct" | "incorrect") {
    if (!response) return;
    updateQueryFeedback(response.request_id, value);
    setFeedback(value);
  }

  return (
    <main className="workspace-page">
      <section className="container workspace-header">
        <div>
          <p className="eyebrow">QUERY WORKSPACE</p>
          <h1>Ask a business question</h1>
          <p>
            SafeQuery AI generates PostgreSQL, validates it, and returns
            the result with an inspectable confidence report.
          </p>
        </div>

        <div className="workspace-security">
          <ShieldCheck size={20} />
          <div>
            <strong>Protected execution</strong>
            <small>Read-only PostgreSQL account</small>
          </div>
        </div>
      </section>

      <section className="container workspace-grid">
        <div className="query-column">
          <form className="query-card" onSubmit={handleSubmit}>
            <label htmlFor="query-question">Business question</label>
            <textarea
              id="query-question"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              rows={5}
              disabled={loading}
            />

            <div className="example-row">
              {EXAMPLES.map((example) => (
                <button
                  key={example}
                  type="button"
                  onClick={() => setQuestion(example)}
                  disabled={loading}
                >
                  {example}
                </button>
              ))}
            </div>

            <div className="query-actions">
              <label className="switch-row">
                <input
                  type="checkbox"
                  checked={runMultiQuery}
                  onChange={(event) =>
                    setRunMultiQuery(event.target.checked)
                  }
                />
                <span>Independent validation for complex queries</span>
              </label>

              <button
                className="button button-primary button-large"
                type="submit"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <LoaderCircle className="spin" size={18} />
                    Analyzing
                  </>
                ) : (
                  <>
                    Run query
                    <Database size={18} />
                  </>
                )}
              </button>
            </div>
          </form>

          {error && (
            <div className="form-error standalone">
              <strong>Request failed</strong>
              <p>{error}</p>
            </div>
          )}

          {response && (
            <>
              <section className="result-summary">
                <div>
                  <span className={`status-pill status-${response.status}`}>
                    {formatLabel(response.status)}
                  </span>
                  <h2>{response.summary}</h2>
                  <p>{response.explanation}</p>
                </div>

                <button
                  type="button"
                  className="icon-button"
                  onClick={() => {
                    setResponse(null);
                    setError("");
                  }}
                  title="Clear result"
                  aria-label="Clear result"
                >
                  <RotateCcw size={18} />
                </button>
              </section>

              <section className="metrics-grid">
                <article>
                  <small>Confidence</small>
                  <strong>
                    {response.confidence_percent === null
                      ? "Not calculated"
                      : `${response.confidence_percent.toFixed(1)}%`}
                  </strong>
                  <span>
                    {response.confidence_label
                      ? `${formatLabel(response.confidence_label)} confidence`
                      : "No score"}
                  </span>
                </article>

                <article>
                  <small>Hallucination risk</small>
                  <strong>
                    {response.hallucination_risk
                      ? formatLabel(response.hallucination_risk)
                      : "Not checked"}
                  </strong>
                  <span>
                    {response.hallucination_detected
                      ? "Review required"
                      : "No issue detected"}
                  </span>
                </article>

                <article>
                  <small>Rows</small>
                  <strong>{response.row_count}</strong>
                  <span>
                    {response.result_hidden
                      ? "Rows hidden"
                      : "Rows returned"}
                  </span>
                </article>

                <article>
                  <small>Total time</small>
                  <strong>{response.timings.total_ms.toFixed(0)} ms</strong>
                  <span>
                    {response.timings.generation_ms.toFixed(0)} ms generation
                  </span>
                </article>
              </section>

              {(response.safe_sql || response.generated_sql) && (
                <section className="workspace-card">
                  <div className="card-heading">
                    <div>
                      <p className="eyebrow">GENERATED SQL</p>
                      <h3>Validated query</h3>
                    </div>

                    <button
                      type="button"
                      className="button button-secondary"
                      onClick={copySql}
                    >
                      {copied ? <Check size={16} /> : <Clipboard size={16} />}
                      {copied ? "Copied" : "Copy SQL"}
                    </button>
                  </div>

                  <pre className="sql-view">
                    <code>{response.safe_sql ?? response.generated_sql}</code>
                  </pre>

                  <div className="tag-row">
                    {response.tables_used.map((table) => (
                      <span key={table}>{table}</span>
                    ))}
                  </div>
                </section>
              )}

              <section className="workspace-card">
                <div className="card-heading">
                  <div>
                    <p className="eyebrow">DATABASE OUTPUT</p>
                    <h3>Query result</h3>
                  </div>
                  <span className="muted-label">
                    {response.row_count} row
                    {response.row_count === 1 ? "" : "s"}
                  </span>
                </div>

                {response.result_hidden ? (
                  <div className="empty-result">
                    <strong>Results hidden</strong>
                    <p>
                      Validation did not meet the configured display
                      requirements. Review the warnings below.
                    </p>
                  </div>
                ) : response.rows.length === 0 ? (
                  <div className="empty-result">
                    <strong>No rows returned</strong>
                    <p>The approved query completed successfully.</p>
                  </div>
                ) : (
                  <div className="table-shell">
                    <table>
                      <thead>
                        <tr>
                          {response.result_columns.map((column) => (
                            <th key={column}>{formatLabel(column)}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {response.rows.map((row, rowIndex) => (
                          <tr key={rowIndex}>
                            {response.result_columns.map((column) => (
                              <td key={`${rowIndex}-${column}`}>
                                {formatValue(row[column])}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {!response.result_hidden && response.rows.length > 0 && (
                  <div className="feedback-bar">
                    <span>Was this result correct?</span>
                    <button
                      type="button"
                      className={feedback === "correct" ? "selected" : ""}
                      onClick={() => recordFeedback("correct")}
                    >
                      <ThumbsUp size={16} />
                      Correct
                    </button>
                    <button
                      type="button"
                      className={feedback === "incorrect" ? "selected" : ""}
                      onClick={() => recordFeedback("incorrect")}
                    >
                      <ThumbsDown size={16} />
                      Incorrect
                    </button>
                  </div>
                )}
              </section>

              {confidenceSignals.length > 0 && (
                <section className="workspace-card">
                  <div className="card-heading">
                    <div>
                      <p className="eyebrow">CONFIDENCE REPORT</p>
                      <h3>Signal breakdown</h3>
                    </div>
                    <span className="muted-label">
                      Multi-query:{" "}
                      {response.multi_query_status
                        ? formatLabel(response.multi_query_status)
                        : "Not checked"}
                    </span>
                  </div>

                  <div className="signal-grid">
                    {confidenceSignals.map((signal) => (
                      <ConfidenceSignalCard
                        key={signal.name}
                        signal={signal}
                      />
                    ))}
                  </div>
                </section>
              )}

              {response.warnings.length > 0 && (
                <section className="workspace-card">
                  <div className="card-heading">
                    <div>
                      <p className="eyebrow">SAFETY REPORT</p>
                      <h3>Warnings and review notes</h3>
                    </div>
                  </div>

                  <div className="warning-stack">
                    {response.warnings.map((warning, index) => (
                      <WarningRow
                        key={`${warning.code}-${index}`}
                        warning={warning}
                      />
                    ))}
                  </div>
                </section>
              )}
            </>
          )}
        </div>

        <aside className="workspace-aside">
          <div className="aside-card">
            <p className="eyebrow">QUERY GUIDANCE</p>
            <h3>Write a precise request</h3>
            <ul>
              <li>State the metric you want.</li>
              <li>Name the grouping or dimension.</li>
              <li>Include dates when relevant.</li>
              <li>Use customer city and shipping city carefully.</li>
            </ul>
          </div>

          <div className="aside-card">
            <p className="eyebrow">ACTIVE CONTROLS</p>
            <dl>
              <div>
                <dt>SQL safety</dt>
                <dd>Enabled</dd>
              </div>
              <div>
                <dt>Read-only execution</dt>
                <dd>Enabled</dd>
              </div>
              <div>
                <dt>Hallucination check</dt>
                <dd>Enabled</dd>
              </div>
              <div>
                <dt>Row limit</dt>
                <dd>1,000</dd>
              </div>
            </dl>
          </div>
        </aside>
      </section>
    </main>
  );
}