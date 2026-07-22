import { Link } from "react-router-dom";
import logo from "../assets/safequery-logo.svg";

export function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <Link className="brand-lockup" to="/" aria-label="SafeQuery AI home">
      <img src={logo} alt="" className="brand-mark" />

      {!compact && (
        <span className="brand-copy">
          <strong>SafeQuery AI</strong>
          <small>Trusted database intelligence</small>
        </span>
      )}
    </Link>
  );
}