import { ArrowRight, ShieldCheck } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

export function SignupPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const { signup } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (password.length < 8) {
      setError("Use at least eight characters for the password.");
      return;
    }

    setSubmitting(true);
    setError("");

    try {
      await signup(name, email, password);
      navigate("/workspace", { replace: true });
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Account creation failed.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-panel">
        <div className="auth-intro">
          <span className="feature-icon">
            <ShieldCheck size={22} />
          </span>
          <p className="eyebrow">CREATE YOUR WORKSPACE</p>
          <h1>Start with safe, explainable database analytics</h1>
          <p>
            Your local account keeps the workspace, theme preference,
            query history, and result feedback together on this browser.
          </p>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label>
            Full name
            <input
              type="text"
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="Your name"
              autoComplete="name"
              required
            />
          </label>

          <label>
            Email address
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="name@example.com"
              autoComplete="email"
              required
            />
          </label>

          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Minimum eight characters"
              autoComplete="new-password"
              minLength={8}
              required
            />
          </label>

          {error && <div className="form-error">{error}</div>}

          <button
            className="button button-primary button-large full-width"
            type="submit"
            disabled={submitting}
          >
            {submitting ? "Creating account..." : "Create account"}
            {!submitting && <ArrowRight size={18} />}
          </button>

          <p className="auth-switch">
            Already registered? <Link to="/login">Log in</Link>
          </p>
        </form>
      </section>
    </main>
  );
}