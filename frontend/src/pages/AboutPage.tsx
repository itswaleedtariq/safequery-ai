import {
  Code2,
  Database,
  ExternalLink,
  GraduationCap,
  ServerCog,
} from "lucide-react";

export function AboutPage() {
  return (
    <main>
      <section className="page-hero">
        <div className="container narrow">
          <p className="eyebrow">ABOUT THE PROJECT</p>
          <h1>Production-minded AI for safer data access</h1>
          <p>
            SafeQuery AI was created to make natural-language database
            analytics useful without treating model output as inherently
            trustworthy.
          </p>
        </div>
      </section>

      <section className="section">
        <div className="container about-grid">
          <article className="about-story">
            <p className="eyebrow">PROJECT OVERVIEW</p>
            <h2>Why SafeQuery AI exists</h2>

            <p>
              Text-to-SQL is valuable because it gives non-technical
              users faster access to business data. It is also risky:
              generated SQL can be destructive, expensive, or simply
              answer the wrong question.
            </p>

            <p>
              This project addresses those risks with schema-aware
              generation, static guardrails, PostgreSQL read-only
              execution, query-plan checks, hallucination detection, and
              explainable confidence scoring.
            </p>

            <div className="technology-list">
              <span><Code2 size={17} /> FastAPI and React</span>
              <span><Database size={17} /> PostgreSQL 17</span>
              <span><ServerCog size={17} /> Docker and CI-ready tests</span>
            </div>
          </article>

          <aside className="author-card">
            <div className="author-initials">WT</div>
            <p className="eyebrow">AUTHOR</p>
            <h2>Waleed Tariq</h2>
            <p className="author-role">
              Software Engineering undergraduate at GIKI
            </p>

            <p>
              I focus on AI engineering, backend systems, web
              development, and DevOps. My work combines Python,
              FastAPI, Django, React, PostgreSQL, Docker, CI/CD, and
              cloud tooling to build practical, production-oriented
              software.
            </p>

            <div className="author-meta">
              <span>
                <GraduationCap size={17} />
                BS Software Engineering
              </span>
            </div>

            <a
              className="button button-secondary"
              href="https://github.com/itswaleedtariq"
              target="_blank"
              rel="noreferrer"
            >
              View GitHub
              <ExternalLink size={16} />
            </a>
          </aside>
        </div>
      </section>
    </main>
  );
}