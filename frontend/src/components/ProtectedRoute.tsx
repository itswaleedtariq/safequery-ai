import type { ReactNode } from "react";

import {
  Navigate,
  useLocation,
} from "react-router-dom";

import { useAuth } from "../context/AuthContext";

export function ProtectedRoute({
  children,
}: {
  children: ReactNode;
}) {
  const {
    user,
    loading,
  } = useAuth();

  const location = useLocation();

  if (loading) {
    return (
      <main className="auth-page">
        <section className="feature-card">
          <p className="eyebrow">
            SAFEQUERY AI
          </p>

          <h2>
            Verifying your session
          </h2>

          <p>
            Please wait while your account is
            authenticated.
          </p>
        </section>
      </main>
    );
  }

  if (!user) {
    return (
      <Navigate
        to="/login"
        replace
        state={{
          from: location.pathname,
        }}
      />
    );
  }

  return children;
}