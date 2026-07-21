import { useState } from "react";
import type { FormEvent } from "react";

import { submitQuery } from "./api";
import type {
  ConfidenceSignal,
  QueryWorkflowResponse,
  WorkflowWarning,
} from "./types";

import "./App.css";


const EXAMPLE_QUESTIONS = [
  "How many customers are there?",
  "Which five products generated the highest revenue?",
  "Show the total number of completed orders.",
  "What is the average order value?",
];


function formatLabel(value: string): string {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) =>
      character.toUpperCase(),
    );
}


function formatValue(value: unknown): string {
  if (value === null || value === undefined) {
    return "NULL";
  }

  if (typeof value === "object") {
    return JSON.stringify(value);
  }

  return String(value);
}


function StatusBadge({
  status,
}: {
  status: QueryWorkflowResponse["status"];
}) {
  return (
    <span className={`status-badge status-${status}`}>
      {formatLabel(status)}
    </span>
  );
}


function MetricCard({
  label,
  value,
  helper,
}: {
  label: string;
  value: string;
  helper?: string;
}) {
  return (
    <article className="metric-card">
      <p className="metric-label">{label}</p>
      <strong className="metric-value">{value}</strong>

      {helper && (
        <p className="metric-helper">{helper}</p>
      )}
    </article>
  );
}


function ConfidenceCard({
  signal,
}: {
  signal: ConfidenceSignal;
}) {
  const percentage =
    signal.score === null
      ? 0
      : Math.round(signal.score * 100);

  return (
    <article className="signal-card">
      <div className="signal-heading">
        <strong>{formatLabel(signal.name)}</strong>

        <span>
          {signal.available
            ? `${percentage}%`
            : "Not used"}
        </span>
      </div>

      <div className="progress-track">
        <div
          className="progress-value"
          style={{
            width: `${percentage}%`,
          }}
        />
      </div>

      <p>{signal.explanation}</p>

      <small>
        Effective weight:{" "}
        {Math.round(signal.effective_weight * 100)}%
      </small>
    </article>
  );
}


function WarningCard({
  warning,
}: {
  warning: WorkflowWarning;
}) {
  return (
    <article
      className={`warning-card warning-${warning.severity}`}
    >
      <div>
        <strong>{formatLabel(warning.code)}</strong>
        <span>{warning.severity}</span>
      </div>

      <p>{warning.message}</p>
    </article>
  );
}


function ResultsTable({
  response,
}: {
  response: QueryWorkflowResponse;
}) {
  if (response.result_hidden) {
    return (
      <div className="empty-state">
        <strong>Results hidden</strong>

        <p>
          The result did not meet the confidence and safety
          requirements.
        </p>
      </div>
    );
  }

  if (response.rows.length === 0) {
    return (
      <div className="empty-state">
        <strong>No rows returned</strong>

        <p>
          The query completed without returning any records.
        </p>
      </div>
    );
  }

  return (
    <div className="table-container">
      <table>
        <thead>
          <tr>
            {response.result_columns.map((column) => (
              <th key={column}>
                {formatLabel(column)}
              </th>
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
  );
}


function App() {
  const [question, setQuestion] = useState(
    "Which five products generated the highest revenue?",
  );

  const [runMultiQuery, setRunMultiQuery] =
    useState(true);

  const [response, setResponse] =
    useState<QueryWorkflowResponse | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");


  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    const trimmedQuestion = question.trim();

    if (!trimmedQuestion) {
      setError("Enter a business question.");
      return;
    }

    setLoading(true);
    setError("");
    setResponse(null);

    try {
      const result = await submitQuery({
        question: trimmedQuestion,
        max_tables: 4,
        max_examples: 3,
        run_multi_query: runMultiQuery,
      });

      setResponse(result);
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
    const sql =
      response?.safe_sql ??
      response?.generated_sql;

    if (!sql) {
      return;
    }

    await navigator.clipboard.writeText(sql);
  }


  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-icon">SQ</div>

          <div>
            <h1>SafeQuery AI</h1>
            <p>Secure Text-to-SQL Analytics</p>
          </div>
        </div>

        <span className="version-badge">
          v1.1.0
        </span>
      </header>

      <section className="hero">
        <div>
          <p className="eyebrow">
            AI DATABASE ANALYST
          </p>

          <h2>
            Ask business questions without writing SQL.
          </h2>

          <p className="hero-description">
            SafeQuery AI generates PostgreSQL queries,
            validates their safety, executes them through a
            read-only database account, and calculates an
            explainable confidence score.
          </p>
        </div>
      </section>

      <section className="query-panel">
        <form onSubmit={handleSubmit}>
          <label htmlFor="question">
            Business question
          </label>

          <textarea
            id="question"
            value={question}
            onChange={(event) =>
              setQuestion(event.target.value)
            }
            placeholder="Ask a question about the database..."
            rows={4}
            disabled={loading}
          />

          <div className="example-list">
            {EXAMPLE_QUESTIONS.map((example) => (
              <button
                key={example}
                type="button"
                className="example-button"
                onClick={() => setQuestion(example)}
                disabled={loading}
              >
                {example}
              </button>
            ))}
          </div>

          <div className="form-actions">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={runMultiQuery}
                onChange={(event) =>
                  setRunMultiQuery(
                    event.target.checked,
                  )
                }
                disabled={loading}
              />

              Validate complex queries independently
            </label>

            <button
              className="submit-button"
              type="submit"
              disabled={loading}
            >
              {loading
                ? "Analyzing query..."
                : "Run SafeQuery"}
            </button>
          </div>
        </form>
      </section>

      {error && (
        <section className="error-banner">
          <strong>Request failed</strong>
          <p>{error}</p>
        </section>
      )}

      {loading && (
        <section className="loading-panel">
          <div className="loader" />

          <div>
            <strong>
              Analyzing your question
            </strong>

            <p>
              Generating SQL, applying guardrails and
              calculating confidence.
            </p>
          </div>
        </section>
      )}

      {response && (
        <div className="response-layout">
          <section className="response-header">
            <div>
              <StatusBadge
                status={response.status}
              />

              <h2>{response.summary}</h2>

              <p>{response.explanation}</p>
            </div>

            <div className="request-id">
              Request
              <code>
                {response.request_id.slice(0, 8)}
              </code>
            </div>
          </section>

          {response.clarification_question && (
            <section className="clarification-panel">
              <strong>
                Clarification required
              </strong>

              <p>
                {response.clarification_question}
              </p>
            </section>
          )}

          <section className="metrics-grid">
            <MetricCard
              label="Confidence"
              value={
                response.confidence_percent === null
                  ? "Not calculated"
                  : `${response.confidence_percent.toFixed(
                      1,
                    )}%`
              }
              helper={
                response.confidence_label
                  ? `${formatLabel(
                      response.confidence_label,
                    )} confidence`
                  : undefined
              }
            />

            <MetricCard
              label="Hallucination risk"
              value={
                response.hallucination_risk
                  ? formatLabel(
                      response.hallucination_risk,
                    )
                  : "Not checked"
              }
              helper={
                response.hallucination_detected
                  ? "Possible hallucination detected"
                  : "No hallucination detected"
              }
            />

            <MetricCard
              label="Rows"
              value={String(response.row_count)}
              helper={
                response.result_hidden
                  ? "Rows are hidden"
                  : "Rows returned"
              }
            />

            <MetricCard
              label="Total time"
              value={`${response.timings.total_ms.toFixed(
                0,
              )} ms`}
              helper={`${response.timings.generation_ms.toFixed(
                0,
              )} ms generation`}
            />
          </section>

          {(response.safe_sql ||
            response.generated_sql) && (
            <section className="content-card">
              <div className="section-heading">
                <div>
                  <p className="section-label">
                    GENERATED QUERY
                  </p>

                  <h3>SQL</h3>
                </div>

                <button
                  type="button"
                  className="secondary-button"
                  onClick={copySql}
                >
                  Copy SQL
                </button>
              </div>

              <pre className="sql-block">
                <code>
                  {response.safe_sql ??
                    response.generated_sql}
                </code>
              </pre>

              <div className="tag-list">
                {response.tables_used.map(
                  (table) => (
                    <span
                      key={table}
                      className="tag"
                    >
                      {table}
                    </span>
                  ),
                )}
              </div>
            </section>
          )}

          <section className="content-card">
            <div className="section-heading">
              <div>
                <p className="section-label">
                  DATABASE OUTPUT
                </p>

                <h3>Query results</h3>
              </div>

              <span>
                {response.row_count} row
                {response.row_count === 1
                  ? ""
                  : "s"}
              </span>
            </div>

            <ResultsTable response={response} />
          </section>

          {response.confidence_signals.length >
            0 && (
            <section className="content-card">
              <div className="section-heading">
                <div>
                  <p className="section-label">
                    VALIDATION
                  </p>

                  <h3>
                    Confidence breakdown
                  </h3>
                </div>

                <span>
                  Multi-query:{" "}
                  {response.multi_query_status
                    ? formatLabel(
                        response.multi_query_status,
                      )
                    : "Not checked"}
                </span>
              </div>

              <div className="signal-grid">
                {response.confidence_signals.map(
                  (signal) => (
                    <ConfidenceCard
                      key={signal.name}
                      signal={signal}
                    />
                  ),
                )}
              </div>
            </section>
          )}

          {response.warnings.length > 0 && (
            <section className="content-card">
              <div className="section-heading">
                <div>
                  <p className="section-label">
                    SAFETY REPORT
                  </p>

                  <h3>
                    Warnings and review notes
                  </h3>
                </div>
              </div>

              <div className="warning-list">
                {response.warnings.map(
                  (warning, index) => (
                    <WarningCard
                      key={`${warning.code}-${index}`}
                      warning={warning}
                    />
                  ),
                )}
              </div>
            </section>
          )}

          <section className="content-card metadata-card">
            <h3>Execution metadata</h3>

            <dl>
              <div>
                <dt>Provider</dt>
                <dd>
                  {response.provider ?? "Unknown"}
                </dd>
              </div>

              <div>
                <dt>Model</dt>
                <dd>
                  {response.model ?? "Unknown"}
                </dd>
              </div>

              <div>
                <dt>Guardrail</dt>
                <dd>
                  {response.guardrail_allowed === null
                    ? "Not checked"
                    : response.guardrail_allowed
                      ? "Allowed"
                      : "Blocked"}
                </dd>
              </div>

              <div>
                <dt>Confidence pipeline</dt>
                <dd>
                  {response.timings.confidence_pipeline_ms.toFixed(
                    0,
                  )}{" "}
                  ms
                </dd>
              </div>
            </dl>
          </section>
        </div>
      )}
    </main>
  );
}


export default App;