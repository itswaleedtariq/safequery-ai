import {
  ArrowRight,
  CheckCircle2,
  Database,
  Gauge,
  SearchCheck,
  ShieldCheck,
} from "lucide-react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const features = [
  {
    icon: ShieldCheck,
    title: "Guarded SQL generation",
    text: "Every generated query is parsed, checked, limited, and approved before execution.",
  },
  {
    icon: Database,
    title: "Read-only database access",
    text: "Queries execute through a dedicated PostgreSQL account with SELECT-only permissions.",
  },
  {
    icon: SearchCheck,
    title: "Hallucination detection",
    text: "The system checks whether the SQL actually answers the original business question.",
  },
  {
    icon: Gauge,
    title: "Explainable confidence",
    text: "Alignment, schema coverage, result sanity, and query agreement contribute to one score.",
  },
];

const workflow = [
  "Understand the business question",
  "Select relevant schema context",
  "Generate structured PostgreSQL",
  "Apply safety and cost guardrails",
  "Execute with read-only permissions",
  "Return results with confidence",
];

export function HomePage() {
  const { user } = useAuth();

  return (
    <main>
      <section className="hero-section">
        <div className="container hero-grid">
          <div className="hero-copy">
            <p className="eyebrow">SECURE TEXT-TO-SQL ANALYTICS</p>

            <h1>
              Ask the database in plain English.
              <span> Keep every query accountable.</span>
            </h1>

            <p className="hero-lead">
              SafeQuery AI translates business questions into
              PostgreSQL, validates the query, executes it safely, and
              explains how much confidence you should place in the
              result.
            </p>

            <div className="hero-actions">
              <Link
                className="button button-primary button-large"
                to={user ? "/workspace" : "/signup"}
              >
                Start querying
                <ArrowRight size={18} />
              </Link>

              <Link
                className="button button-secondary button-large"
                to="/about"
              >
                View project overview
              </Link>
            </div>

            <div className="trust-row">
              <span><CheckCircle2 size={16} /> Read-only execution</span>
              <span><CheckCircle2 size={16} /> SQL guardrails</span>
              <span><CheckCircle2 size={16} /> Confidence scoring</span>
            </div>
          </div>

          <div className="hero-product-card">
            <div className="terminal-header">
              <div>
                <small>Business question</small>
                <strong>Which products generated the highest revenue?</strong>
              </div>
              <span className="status-pill">Validated</span>
            </div>

            <pre>
              <code>{`SELECT
  p.name,
  SUM(oi.line_total) AS revenue
FROM products AS p
JOIN order_items AS oi ON oi.product_id = p.id
JOIN orders AS o ON o.id = oi.order_id
WHERE o.status IN ('completed', 'shipped')
GROUP BY p.id, p.name
ORDER BY revenue DESC
LIMIT 5;`}</code>
            </pre>

            <div className="product-metrics">
              <div>
                <small>Confidence</small>
                <strong>94%</strong>
              </div>
              <div>
                <small>Guardrail</small>
                <strong>Passed</strong>
              </div>
              <div>
                <small>Risk</small>
                <strong>Low</strong>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="section section-muted">
        <div className="container">
          <div className="section-heading centered">
            <p className="eyebrow">BUILT FOR TRUST</p>
            <h2>More than a SQL generator</h2>
            <p>
              SafeQuery AI treats generated SQL as untrusted input and
              validates each stage before showing the result.
            </p>
          </div>

          <div className="feature-grid">
            {features.map(({ icon: Icon, title, text }) => (
              <article className="feature-card" key={title}>
                <span className="feature-icon">
                  <Icon size={22} />
                </span>
                <h3>{title}</h3>
                <p>{text}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="section">
        <div className="container split-section">
          <div>
            <p className="eyebrow">HOW IT WORKS</p>
            <h2>A traceable path from question to answer</h2>
            <p className="section-copy">
              Each stage produces metadata that can be inspected in the
              workspace, including the generated SQL, referenced tables,
              confidence signals, warnings, and timings.
            </p>
          </div>

          <ol className="workflow-list">
            {workflow.map((step, index) => (
              <li key={step}>
                <span>{String(index + 1).padStart(2, "0")}</span>
                <p>{step}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section className="section">
        <div className="container cta-panel">
          <div>
            <p className="eyebrow">READY TO USE</p>
            <h2>Move from a question to a validated result.</h2>
            <p>
              Open the workspace, choose a sample question, or write your
              own analytics request.
            </p>
          </div>

          <Link
            className="button button-primary button-large"
            to={user ? "/workspace" : "/signup"}
          >
            Open SafeQuery AI
            <ArrowRight size={18} />
          </Link>
        </div>
      </section>
    </main>
  );
}