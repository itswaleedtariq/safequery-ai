import { Menu, X } from "lucide-react";
import { useState } from "react";
import {
  Link,
  NavLink,
  Outlet,
  useNavigate,
} from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { Logo } from "./Logo";
import { ThemeToggle } from "./ThemeToggle";

const navItems = [
  { to: "/", label: "Home" },
  { to: "/about", label: "About" },
];

export function AppShell() {
  const [menuOpen, setMenuOpen] = useState(false);
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function signOut() {
    logout();
    setMenuOpen(false);
    navigate("/");
  }

  return (
    <div className="site-frame">
      <header className="site-header">
        <div className="container nav-shell">
          <Logo />

          <nav className={`main-nav ${menuOpen ? "is-open" : ""}`}>
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={() => setMenuOpen(false)}
              >
                {item.label}
              </NavLink>
            ))}

            {user && (
              <>
                <NavLink
                  to="/workspace"
                  onClick={() => setMenuOpen(false)}
                >
                  Workspace
                </NavLink>
                <NavLink
                  to="/history"
                  onClick={() => setMenuOpen(false)}
                >
                  History
                </NavLink>
              </>
            )}
          </nav>

          <div className="nav-actions">
            <ThemeToggle />

            {user ? (
              <>
                <span className="user-chip">
                  {user.name.split(" ")[0]}
                </span>
                <button
                  type="button"
                  className="button button-ghost desktop-action"
                  onClick={signOut}
                >
                  Sign out
                </button>
              </>
            ) : (
              <>
                <Link
                  className="button button-ghost desktop-action"
                  to="/login"
                >
                  Log in
                </Link>
                <Link
                  className="button button-primary desktop-action"
                  to="/signup"
                >
                  Create account
                </Link>
              </>
            )}

            <button
              type="button"
              className="icon-button mobile-menu-button"
              onClick={() => setMenuOpen((current) => !current)}
              aria-label="Toggle navigation"
            >
              {menuOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </div>
      </header>

      <Outlet />

      <footer className="site-footer">
        <div className="container footer-grid">
          <div>
            <Logo />
            <p>
              A secure natural-language interface for PostgreSQL
              analytics with layered validation.
            </p>
          </div>

          <div className="footer-links">
            <Link to="/about">About</Link>
            <Link to={user ? "/workspace" : "/login"}>Open workspace</Link>
            <a
              href="https://github.com/itswaleedtariq"
              target="_blank"
              rel="noreferrer"
            >
              GitHub
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}