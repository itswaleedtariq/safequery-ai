import {
  ArrowRight,
  LockKeyhole,
} from "lucide-react";

import {
  useState,
  type FormEvent,
} from "react";

import {
  Link,
  Navigate,
  useLocation,
  useNavigate,
} from "react-router-dom";

import { useAuth } from "../context/AuthContext";

interface LocationState {
  from?: string;
}

export function LoginPage() {
  const [email, setEmail] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [error, setError] =
    useState("");

  const [submitting, setSubmitting] =
    useState(false);

  const {
    login,
    user,
    loading,
  } = useAuth();

  const navigate = useNavigate();
  const location = useLocation();

  if (loading) {
    return (
      <main className="auth-page">
        <section className="feature-card">
          <p>Checking your session...</p>
        </section>
      </main>
    );
  }

  if (user) {
    return (
      <Navigate
        to="/workspace"
        replace
      />
    );
  }

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setSubmitting(true);
    setError("");

    try {
      await login(
        email,
        password,
      );

      const state =
        location.state as LocationState | null;

      navigate(
        state?.from ?? "/workspace",
        {
          replace: true,
        },
      );
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Login failed.",
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
            <LockKeyhole size={22} />
          </span>

          <p className="eyebrow">
            WELCOME BACK
          </p>

          <h1>
            Continue to your query workspace
          </h1>

          <p>
            Sign in to access your SafeQuery
            workspace and protected database
            analysis tools.
          </p>
        </div>

        <form
          className="auth-form"
          onSubmit={handleSubmit}
        >
          <label>
            Email address

            <input
              type="email"
              value={email}
              onChange={(event) =>
                setEmail(event.target.value)
              }
              placeholder="name@example.com"
              autoComplete="email"
              disabled={submitting}
              required
            />
          </label>

          <label>
            Password

            <input
              type="password"
              value={password}
              onChange={(event) =>
                setPassword(event.target.value)
              }
              placeholder="Enter your password"
              autoComplete="current-password"
              minLength={8}
              disabled={submitting}
              required
            />
          </label>

          {error && (
            <div
              className="form-error"
              role="alert"
            >
              {error}
            </div>
          )}

          <button
            className="button button-primary button-large full-width"
            type="submit"
            disabled={submitting}
          >
            {submitting
              ? "Signing in..."
              : "Log in"}

            {!submitting && (
              <ArrowRight size={18} />
            )}
          </button>

          <p className="auth-switch">
            New to SafeQuery AI?{" "}

            <Link to="/signup">
              Create an account
            </Link>
          </p>
        </form>
      </section>
    </main>
  );
}