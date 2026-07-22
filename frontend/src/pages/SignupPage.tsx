import {
  ArrowRight,
  ShieldCheck,
} from "lucide-react";

import {
  useState,
  type FormEvent,
} from "react";

import {
  Link,
  Navigate,
  useNavigate,
} from "react-router-dom";

import { useAuth } from "../context/AuthContext";

export function SignupPage() {
  const [name, setName] =
    useState("");

  const [email, setEmail] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [confirmPassword, setConfirmPassword] =
    useState("");

  const [error, setError] =
    useState("");

  const [submitting, setSubmitting] =
    useState(false);

  const {
    signup,
    user,
    loading,
  } = useAuth();

  const navigate = useNavigate();

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

    setError("");

    if (password.length < 8) {
      setError(
        "Password must contain at least eight characters.",
      );

      return;
    }

    if (password !== confirmPassword) {
      setError(
        "Password confirmation does not match.",
      );

      return;
    }

    setSubmitting(true);

    try {
      await signup(
        name,
        email,
        password,
      );

      navigate(
        "/workspace",
        {
          replace: true,
        },
      );
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

          <p className="eyebrow">
            CREATE YOUR ACCOUNT
          </p>

          <h1>
            Start using protected database analytics
          </h1>

          <p>
            Create a SafeQuery AI account to
            access the authenticated query
            workspace and saved analysis tools.
          </p>
        </div>

        <form
          className="auth-form"
          onSubmit={handleSubmit}
        >
          <label>
            Full name

            <input
              type="text"
              value={name}
              onChange={(event) =>
                setName(event.target.value)
              }
              placeholder="Your name"
              autoComplete="name"
              minLength={2}
              maxLength={120}
              disabled={submitting}
              required
            />
          </label>

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
              placeholder="Minimum eight characters"
              autoComplete="new-password"
              minLength={8}
              maxLength={128}
              disabled={submitting}
              required
            />
          </label>

          <label>
            Confirm password

            <input
              type="password"
              value={confirmPassword}
              onChange={(event) =>
                setConfirmPassword(
                  event.target.value,
                )
              }
              placeholder="Repeat your password"
              autoComplete="new-password"
              minLength={8}
              maxLength={128}
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
              ? "Creating account..."
              : "Create account"}

            {!submitting && (
              <ArrowRight size={18} />
            )}
          </button>

          <p className="auth-switch">
            Already registered?{" "}

            <Link to="/login">
              Log in
            </Link>
          </p>
        </form>
      </section>
    </main>
  );
}